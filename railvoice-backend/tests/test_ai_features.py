"""Generative-AI features, run against the deterministic fake client."""

import pytest
from httpx import AsyncClient

from app.ai.client import AIUnavailable, FakeClient, set_ai

API = "/api/v1"


@pytest.fixture
def fake_ai():
    client = FakeClient()
    set_ai(client)
    yield client
    set_ai(None)


@pytest.mark.asyncio
async def test_ai_off_by_default(client: AsyncClient, auth_headers):
    assert (await client.get(f"{API}/ai/status")).json()["data"]["enabled"] is False
    res = await client.post(f"{API}/ai/draft-report", headers=auth_headers, json={"note": "lift broken"})
    assert res.status_code == 503


@pytest.mark.asyncio
async def test_draft_report(client: AsyncClient, auth_headers, bandra_station_id, fake_ai):
    assert (await client.get(f"{API}/ai/status")).json()["data"]["enabled"] is True
    res = await client.post(
        f"{API}/ai/draft-report",
        headers=auth_headers,
        json={"note": "platform 3 pe escalator band hai since morning", "station_id": bandra_station_id},
    )
    assert res.status_code == 200
    draft = res.json()["data"]
    assert draft["category_code"] == "lifts_escalators"
    assert draft["is_emergency"] is False
    prompt = fake_ai.calls[-1]
    assert "Bandra" in prompt.text
    assert "lifts_escalators" in prompt.text  # allowed categories are listed


@pytest.mark.asyncio
async def test_draft_report_needs_identity(client: AsyncClient, fake_ai):
    assert (await client.post(f"{API}/ai/draft-report", json={"note": "lift broken"})).status_code == 401


@pytest.mark.asyncio
async def test_unknown_category_is_corrected(client: AsyncClient, auth_headers, fake_ai):
    fake_ai.handlers["draft_report"] = lambda p: {
        "title": "x", "description": "y", "category_code": "made_up", "is_emergency": False,
        "emergency_reason": "", "language": "en", "is_railway_problem": True,
    }
    res = await client.post(f"{API}/ai/draft-report", headers=auth_headers, json={"note": "something odd here"})
    assert res.json()["data"]["category_code"] == "other"


@pytest.mark.asyncio
async def test_ai_failure_returns_503(client: AsyncClient, auth_headers, fake_ai):
    def boom(_):
        raise AIUnavailable("AI request failed")

    fake_ai.handlers["draft_report"] = boom
    res = await client.post(f"{API}/ai/draft-report", headers=auth_headers, json={"note": "lift broken again"})
    assert res.status_code == 503


class _Block:
    def __init__(self, text):
        self.type = "text"
        self.text = text


class _Response:
    def __init__(self, text, stop_reason="end_turn"):
        self.content = [_Block(text)]
        self.stop_reason = stop_reason


@pytest.mark.asyncio
async def test_claude_client_request_shape_and_refusal(monkeypatch):
    from app.ai.client import ClaudeClient, Prompt, obj

    client = ClaudeClient("test-key")
    sent = {}

    async def fake_create(**kwargs):
        sent.update(kwargs)
        return _Response('{"ok": true}')

    monkeypatch.setattr(client._client.beta.messages, "create", fake_create)
    result = await client.json(Prompt(task="t", system="sys", text="hi"), obj({"ok": {"type": "boolean"}}))
    assert result == {"ok": True}
    assert sent["model"] == "claude-opus-5-5"
    assert sent["fallbacks"] == "default"
    assert sent["betas"] == ["server-side-fallback-2026-07-01"]
    assert sent["output_config"]["format"]["type"] == "json_schema"
    assert "thinking" not in sent and "temperature" not in sent

    async def refuse(**kwargs):
        return _Response("", stop_reason="refusal")

    monkeypatch.setattr(client._client.beta.messages, "create", refuse)
    with pytest.raises(AIUnavailable):
        await client.text(Prompt(task="t", system="sys", text="hi"))


async def _passenger(client):
    import uuid

    mobile = "+91" + str(uuid.uuid4().int)[:10].rjust(10, "7")
    await client.post(f"{API}/auth/otp/request", json={"mobile": mobile})
    res = await client.post(f"{API}/auth/otp/verify", json={"mobile": mobile, "otp": "123456"})
    return {"Authorization": f"Bearer {res.json()['data']['access_token']}"}


@pytest.mark.asyncio
async def test_ai_finds_paraphrased_duplicate(client: AsyncClient, fake_ai):
    import uuid

    reporter = await _passenger(client)
    station = (await client.get(f"{API}/stations?search=Kandivali")).json()["data"][0]["id"]
    marker = uuid.uuid4().hex[:6]
    await client.post(
        f"{API}/issues",
        headers=reporter,
        json={"description": f"Escalator stopped at west exit gate{marker}", "station_id": station},
    )
    res = await client.get(
        f"{API}/issues/similar",
        params={"station_id": station, "q": f"moving stairs not working near west exit gate{marker}"},
    )
    items = res.json()["data"]["items"]
    assert items and items[0]["match_reason"]
    assert fake_ai.calls[-1].task == "same_problem"


@pytest.mark.asyncio
async def test_duplicate_check_falls_back_when_ai_fails(client: AsyncClient, fake_ai):
    def boom(_):
        raise AIUnavailable("down")

    fake_ai.handlers["same_problem"] = boom
    station = (await client.get(f"{API}/stations?search=Bandra")).json()["data"][0]["id"]
    res = await client.get(
        f"{API}/issues/similar", params={"station_id": station, "q": "garbage bins near the foot overbridge"}
    )
    assert res.status_code == 200
    assert all(i["match_reason"] is None for i in res.json()["data"]["items"])


@pytest.mark.asyncio
async def test_suggest_reply_for_staff_only(client: AsyncClient, admin_headers, fake_ai):
    issue_id = (await client.get(f"{API}/issues?limit=1")).json()["data"]["items"][0]["id"]
    res = await client.post(
        f"{API}/ai/suggest-reply",
        headers=admin_headers,
        json={"issue_id": issue_id, "notes": "cleaner sent, done in 30 min", "new_status": "action_started"},
    )
    assert res.status_code == 200
    assert "cleaner sent" in res.json()["data"]["english"]
    assert "action started" in fake_ai.calls[-1].text

    passenger = await _passenger(client)
    denied = await client.post(
        f"{API}/ai/suggest-reply", headers=passenger, json={"issue_id": issue_id, "notes": "hello"}
    )
    assert denied.status_code == 403


@pytest.mark.asyncio
async def test_daily_briefing_is_scoped_and_cached(client: AsyncClient, admin_headers, fake_ai):
    from app.ai import cache

    cache.clear()
    res = await client.get(f"{API}/ai/briefing", headers=admin_headers)
    assert res.status_code == 200
    data = res.json()["data"]
    assert data["headline"]
    calls = len(fake_ai.calls)
    again = await client.get(f"{API}/ai/briefing", headers=admin_headers)
    assert again.json()["data"]["headline"] == data["headline"]
    assert len(fake_ai.calls) == calls  # served from cache

    await client.post(f"{API}/auth/otp/request", json={"mobile": "+919888888888"})
    station_admin = await client.post(
        f"{API}/auth/otp/verify", json={"mobile": "+919888888888", "otp": "123456"}
    )
    headers = {"Authorization": f"Bearer {station_admin.json()['data']['access_token']}"}
    await client.get(f"{API}/ai/briefing", headers=headers)
    sent = fake_ai.calls[-1].text
    rows = [line for line in sent.splitlines() if line.startswith("- ")]
    assert all("| Bandra |" in line for line in rows)


def _jpeg() -> bytes:
    import io

    from PIL import Image

    buffer = io.BytesIO()
    Image.new("RGB", (40, 30), "green").save(buffer, format="JPEG")
    return buffer.getvalue()


@pytest.mark.asyncio
async def test_analyze_photo_sends_image(client: AsyncClient, auth_headers, fake_ai):
    res = await client.post(
        f"{API}/ai/analyze-photo",
        headers=auth_headers,
        files={"file": ("p.jpg", _jpeg(), "image/jpeg")},
    )
    assert res.status_code == 200
    assert res.json()["data"]["category_code"] == "platform_cleanliness"
    prompt = fake_ai.calls[-1]
    assert prompt.images and prompt.images[0].media_type == "image/jpeg"

    bad = await client.post(
        f"{API}/ai/analyze-photo", headers=auth_headers, files={"file": ("x.txt", b"not an image at all", "text/plain")}
    )
    assert bad.status_code == 400


@pytest.mark.asyncio
async def test_ask_cites_only_listed_reports(client: AsyncClient, fake_ai):
    import uuid

    reporter = await _passenger(client)
    station = (await client.get(f"{API}/stations?search=Borivali")).json()["data"][0]["id"]
    marker = uuid.uuid4().hex[:6]
    created = await client.post(
        f"{API}/issues",
        headers=reporter,
        json={"title": f"Escalator{marker} stopped", "description": f"Escalator{marker} near exit stopped", "station_id": station},
    )
    number = created.json()["data"]["issue"]["issue_number"]
    res = await client.post(
        f"{API}/ai/ask", headers=reporter, json={"question": f"is escalator{marker} reported?", "station_id": station}
    )
    assert res.status_code == 200
    data = res.json()["data"]
    assert [i["issue_number"] for i in data["issues"]] == [number]

    fake_ai.handlers["ask"] = lambda p: {"answer": "See RV-MADE-UP", "issue_numbers": ["RV-MADE-UP"]}
    res = await client.post(f"{API}/ai/ask", headers=reporter, json={"question": "anything?"})
    assert res.json()["data"]["issues"] == []
    assert (await client.post(f"{API}/ai/ask", json={"question": "anything?"})).status_code == 401


@pytest.mark.asyncio
async def test_translate_is_cached(client: AsyncClient, fake_ai):
    from app.ai import cache

    cache.clear()
    issue_id = (await client.get(f"{API}/issues?limit=1")).json()["data"]["items"][0]["id"]
    res = await client.get(f"{API}/ai/translate/{issue_id}?lang=hi")
    assert res.status_code == 200
    assert res.json()["data"]["description"].startswith("[Hindi]")
    calls = len(fake_ai.calls)
    await client.get(f"{API}/ai/translate/{issue_id}?lang=hi")
    assert len(fake_ai.calls) == calls
    assert (await client.get(f"{API}/ai/translate/{issue_id}?lang=fr")).status_code == 400


@pytest.mark.asyncio
async def test_station_summary(client: AsyncClient, bandra_station_id, fake_ai):
    from app.ai import cache

    cache.clear()
    res = await client.get(f"{API}/ai/station-summary/{bandra_station_id}")
    assert res.status_code == 200
    assert "Bandra" in res.json()["data"]["summary"]
    rows = [line for line in fake_ai.calls[-1].text.splitlines() if line.startswith("- ")]
    assert all("| Bandra |" in line for line in rows)


async def _new_issue(client, headers, station_search, description, category_code=None):
    station = (await client.get(f"{API}/stations?search={station_search}")).json()["data"][0]["id"]
    body = {"description": description, "station_id": station}
    if category_code:
        body["category_code"] = category_code
    res = await client.post(f"{API}/issues", headers=headers, json=body)
    assert res.status_code == 201, res.text
    return res.json()["data"]["issue"]


@pytest.mark.asyncio
async def test_triage_suggests_department(client: AsyncClient, admin_headers, fake_ai):
    reporter = await _passenger(client)
    issue = await _new_issue(client, reporter, "Dadar", "Escalator near bridge has stopped completely")
    res = await client.post(f"{API}/ai/triage/{issue['id']}", headers=admin_headers)
    assert res.status_code == 200
    assert res.json()["data"]["department"] == "mechanical"
    assert 1 <= res.json()["data"]["urgency"] <= 5
    denied = await client.post(f"{API}/ai/triage/{issue['id']}", headers=reporter)
    assert denied.status_code == 403


@pytest.mark.asyncio
async def test_spam_report_is_flagged_not_hidden(client: AsyncClient, admin_headers, fake_ai):
    reporter = await _passenger(client)
    spam = await _new_issue(client, reporter, "Dadar", "Buy now cheap phones at http://example.com")
    fine = await _new_issue(client, reporter, "Dadar", "Water cooler on platform 2 is leaking badly")
    flags = (await client.get(f"{API}/admin/flags", headers=admin_headers)).json()["data"]["items"]
    by_issue = {f["issue"]["id"] if isinstance(f.get("issue"), dict) else f.get("issue_id"): f for f in flags}
    assert spam["id"] in by_issue
    assert by_issue[spam["id"]]["reporter"] == "AI screening"
    assert by_issue[spam["id"]]["reason"] == "spam"
    assert fine["id"] not in by_issue
    # Still public: AI never removes reports by itself.
    assert (await client.get(f"{API}/issues/{spam['id']}")).status_code == 200


@pytest.mark.asyncio
async def test_screening_failure_does_not_block_reporting(client: AsyncClient, fake_ai):
    def boom(_):
        raise AIUnavailable("down")

    fake_ai.handlers["screen"] = boom
    reporter = await _passenger(client)
    await _new_issue(client, reporter, "Dadar", "Fan not working near ticket window")


@pytest.mark.asyncio
async def test_recurring_problems(client: AsyncClient, admin_headers, fake_ai):
    from app.ai import cache

    cache.clear()
    reporter = await _passenger(client)
    for n in range(3):
        await _new_issue(client, reporter, "Malad", f"Toilet block dirty again, visit {n}", "toilets")
    res = await client.get(f"{API}/ai/recurring", headers=admin_headers)
    assert res.status_code == 200
    items = res.json()["data"]["items"]
    assert items
    assert all(i["count"] >= 3 and i["likely_cause"] for i in items)
    assert [i["count"] for i in items] == sorted((i["count"] for i in items), reverse=True)


@pytest.mark.asyncio
async def test_monthly_report(client: AsyncClient, admin_headers, fake_ai):
    from datetime import datetime, timezone

    from app.ai import cache

    cache.clear()
    month = f"{datetime.now(timezone.utc):%Y-%m}"
    res = await client.get(f"{API}/ai/monthly-report?month={month}", headers=admin_headers)
    assert res.status_code == 200
    data = res.json()["data"]
    assert data["summary"] and data["figures"]["New reports"] >= 1
    assert "New reports" in fake_ai.calls[-1].text
    assert (await client.get(f"{API}/ai/monthly-report?month=bad", headers=admin_headers)).status_code == 400
    assert (await client.get(f"{API}/ai/monthly-report?month=2999-01", headers=admin_headers)).status_code == 400


@pytest.mark.asyncio
async def test_fix_check_compares_photos(client: AsyncClient, admin_headers, fake_ai):
    reporter = await _passenger(client)
    issue = await _new_issue(client, reporter, "Dadar", "Broken bench on platform 1 near stairs")
    missing = await client.post(f"{API}/ai/fix-check/{issue['id']}", headers=admin_headers)
    assert missing.status_code == 400
    files = {"file": ("p.jpg", _jpeg(), "image/jpeg")}
    assert (await client.post(f"{API}/issues/{issue['id']}/photos", headers=reporter, files=files)).status_code == 201
    files = {"file": ("f.jpg", _jpeg(), "image/jpeg")}
    up = await client.post(f"{API}/issues/{issue['id']}/photos?kind=resolution", headers=admin_headers, files=files)
    assert up.status_code == 201
    res = await client.post(f"{API}/ai/fix-check/{issue['id']}", headers=admin_headers)
    assert res.status_code == 200
    assert res.json()["data"]["looks_fixed"] is True
    assert len(fake_ai.calls[-1].images) == 2

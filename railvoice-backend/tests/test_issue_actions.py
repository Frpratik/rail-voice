"""Passenger-side actions: similar reports, withdraw, confirm/reopen, flags, staff alerts."""

import uuid

import pytest
from httpx import AsyncClient

from app.core.config import settings

API = "/api/v1"
STATION_ADMIN_MOBILE = "+919888888888"  # Bandra station admin (seeded)


async def login(client: AsyncClient, mobile: str) -> dict[str, str]:
    await client.post(f"{API}/auth/otp/request", json={"mobile": mobile})
    res = await client.post(f"{API}/auth/otp/verify", json={"mobile": mobile, "otp": "123456"})
    assert res.status_code == 200
    return {"Authorization": f"Bearer {res.json()['data']['access_token']}"}


def new_mobile() -> str:
    return "+91" + str(uuid.uuid4().int)[:10].rjust(10, "7")


async def create_issue(client, headers, station_id, text, category="facilities"):
    res = await client.post(
        f"{API}/issues",
        headers=headers,
        json={"description": text, "station_id": station_id, "category_code": category},
    )
    assert res.status_code == 201, res.text
    return res.json()["data"]["issue"]["id"]


async def advance(client, admin_headers, issue_id, *statuses):
    for status in statuses:
        res = await client.patch(
            f"{API}/admin/issues/{issue_id}/status",
            headers=admin_headers,
            json={"status": status, "remarks": f"moving to {status}"},
        )
        assert res.status_code == 200, res.text


@pytest.mark.asyncio
async def test_similar_issues_found_before_reporting(client, bandra_station_id):
    reporter = await login(client, new_mobile())
    marker = uuid.uuid4().hex[:8]
    text = f"Ticket vending machine {marker} broken near entrance gate"
    await create_issue(client, reporter, bandra_station_id, text)

    res = await client.get(
        f"{API}/issues/similar",
        params={"station_id": bandra_station_id, "category_code": "facilities", "q": f"vending machine {marker} not working"},
    )
    assert res.status_code == 200
    items = res.json()["data"]["items"]
    assert any(marker in i["description"] for i in items)

    unrelated = await client.get(
        f"{API}/issues/similar",
        params={"station_id": bandra_station_id, "q": "zzqx unrelated words qqzz"},
    )
    assert unrelated.json()["data"]["items"] == []


@pytest.mark.asyncio
async def test_reporter_can_withdraw_until_work_starts(client, bandra_station_id, admin_headers):
    reporter = await login(client, new_mobile())
    other = await login(client, new_mobile())
    issue_id = await create_issue(client, reporter, bandra_station_id, "Fan not working at the ladies waiting room")

    assert (await client.post(f"{API}/issues/{issue_id}/withdraw", headers=other, json={})).status_code == 403

    ok = await client.post(f"{API}/issues/{issue_id}/withdraw", headers=reporter, json={"reason": "Fixed itself"})
    assert ok.status_code == 200
    assert ok.json()["data"]["status"] == "withdrawn"

    started = await create_issue(client, reporter, bandra_station_id, "Water cooler leaking on platform one")
    await advance(client, admin_headers, started, "verified", "action_started")
    blocked = await client.post(f"{API}/issues/{started}/withdraw", headers=reporter, json={})
    assert blocked.status_code == 400


@pytest.mark.asyncio
async def test_confirm_fixed_closes_and_not_fixed_reopens(client, bandra_station_id, admin_headers):
    reporter = await login(client, new_mobile())

    fixed_id = await create_issue(client, reporter, bandra_station_id, "Broken bench near platform two stairs")
    early = await client.post(f"{API}/issues/{fixed_id}/confirm", headers=reporter, json={"fixed": True})
    assert early.status_code == 400  # not marked fixed yet

    await advance(client, admin_headers, fixed_id, "verified", "action_started", "completed")
    detail = await client.get(f"{API}/issues/{fixed_id}", headers=reporter)
    assert detail.json()["data"]["viewer"]["can_confirm"] is True

    closed = await client.post(f"{API}/issues/{fixed_id}/confirm", headers=reporter, json={"fixed": True})
    assert closed.json()["data"]["status"] == "closed"

    broken_id = await create_issue(client, reporter, bandra_station_id, "Light flickering over footbridge stairs")
    await advance(client, admin_headers, broken_id, "verified", "action_started", "completed")
    reopened = await client.post(
        f"{API}/issues/{broken_id}/confirm",
        headers=reporter,
        json={"fixed": False, "remarks": "Still flickering tonight"},
    )
    assert reopened.json()["data"]["status"] == "under_review"


@pytest.mark.asyncio
async def test_new_report_notifies_station_staff(client, bandra_station_id):
    staff = await login(client, STATION_ADMIN_MOBILE)
    reporter = await login(client, new_mobile())
    marker = uuid.uuid4().hex[:8]
    await create_issue(client, reporter, bandra_station_id, f"Stray dogs near ticket window {marker} area")

    notes = await client.get(f"{API}/notifications", headers=staff)
    titles = [n["body"] for n in notes.json()["data"]["items"]]
    assert any(marker in t for t in titles)


@pytest.mark.asyncio
async def test_flags_notify_staff_and_admin_can_hide(client, bandra_station_id, admin_headers):
    author = await login(client, new_mobile())
    marker = uuid.uuid4().hex[:8]
    issue_id = await create_issue(client, author, bandra_station_id, f"Totally fake spam report {marker} here")

    own = await client.post(f"{API}/issues/{issue_id}/flag", headers=author, json={"reason": "spam"})
    assert own.status_code == 400  # can't flag your own report

    for _ in range(settings.flag_notify_threshold):
        flagger = await login(client, new_mobile())
        assert (await client.post(f"{API}/issues/{issue_id}/flag", headers=flagger, json={"reason": "spam"})).status_code == 201
    again = await client.post(f"{API}/issues/{issue_id}/flag", headers=flagger, json={"reason": "spam"})
    assert again.status_code == 400  # already flagged

    flags = await client.get(f"{API}/admin/flags", headers=admin_headers)
    mine = [f for f in flags.json()["data"]["items"] if f["issue"]["id"] == issue_id]
    assert len(mine) == settings.flag_notify_threshold

    resolved = await client.post(
        f"{API}/admin/flags/{mine[0]['id']}/resolve", headers=admin_headers, json={"action": "hide"}
    )
    assert resolved.status_code == 200
    assert resolved.json()["data"]["resolved"] == settings.flag_notify_threshold

    hidden = await client.get(f"{API}/issues/{issue_id}")
    assert hidden.status_code == 404
    left = await client.get(f"{API}/admin/flags", headers=admin_headers)
    assert not [f for f in left.json()["data"]["items"] if f["issue"]["id"] == issue_id]


@pytest.mark.asyncio
async def test_daily_report_limit(client, bandra_station_id, monkeypatch):
    monkeypatch.setattr(settings, "daily_issue_limit", 1)
    reporter = await login(client, new_mobile())
    await create_issue(client, reporter, bandra_station_id, "First report of the day about a dirty floor")
    second = await client.post(
        f"{API}/issues",
        headers=reporter,
        json={"description": "Second report of the same day here", "station_id": bandra_station_id},
    )
    assert second.status_code == 400
    assert "Daily limit" in second.json()["detail"]

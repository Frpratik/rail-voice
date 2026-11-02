"""Follows, ratings, reputation, staff tools, analytics and privacy actions."""

import io
import uuid

import pytest
from httpx import AsyncClient
from PIL import Image

API = "/api/v1"


async def login(client: AsyncClient, mobile: str) -> dict[str, str]:
    await client.post(f"{API}/auth/otp/request", json={"mobile": mobile})
    res = await client.post(f"{API}/auth/otp/verify", json={"mobile": mobile, "otp": "123456"})
    assert res.status_code == 200
    return {"Authorization": f"Bearer {res.json()['data']['access_token']}"}


def new_mobile() -> str:
    return "+91" + str(uuid.uuid4().int)[:10].rjust(10, "7")


async def create_issue(client, headers, station_id, text, category="facilities", emergency=False):
    res = await client.post(
        f"{API}/issues",
        headers=headers,
        json={
            "description": text,
            "station_id": station_id,
            "category_code": category,
            "is_emergency": emergency,
        },
    )
    assert res.status_code == 201, res.text
    return res.json()["data"]["issue"]


async def advance(client, admin_headers, issue_id, *statuses):
    for status in statuses:
        res = await client.patch(
            f"{API}/admin/issues/{issue_id}/status",
            headers=admin_headers,
            json={"status": status, "remarks": f"moving to {status}"},
        )
        assert res.status_code == 200, res.text


@pytest.mark.asyncio
async def test_nearest_station(client):
    res = await client.get(f"{API}/stations/nearest", params={"lat": 19.0544, "lng": 72.8406})
    assert res.status_code == 200
    assert res.json()["data"]["items"][0]["code"] == "BA"


@pytest.mark.asyncio
async def test_browsing_needs_no_login_but_anonymous_can_report(client, bandra_station_id):
    assert (await client.get(f"{API}/issues")).status_code == 200
    session = await client.post(f"{API}/auth/anonymous")
    headers = {"X-Anonymous-Session": session.json()["data"]["anonymous_session_id"]}
    issue = await create_issue(client, headers, bandra_station_id, "Anonymous report about a broken tap")
    assert issue["creator"]["is_anonymous"] is True
    # Anonymous users can't back, comment or follow.
    assert (await client.post(f"{API}/issues/{issue['id']}/follow", headers=headers)).status_code == 401


@pytest.mark.asyncio
async def test_followers_are_told_about_status_changes(client, bandra_station_id, admin_headers):
    reporter = await login(client, new_mobile())
    follower = await login(client, new_mobile())
    marker = uuid.uuid4().hex[:8]
    issue = await create_issue(client, reporter, bandra_station_id, f"Follow test leaking roof {marker}")

    res = await client.post(f"{API}/issues/{issue['id']}/follow", headers=follower)
    assert res.json()["data"]["following"] is True
    detail = await client.get(f"{API}/issues/{issue['id']}", headers=follower)
    assert detail.json()["data"]["viewer"]["following"] is True

    following = await client.get(f"{API}/me/following", headers=follower)
    assert issue["id"] in {i["id"] for i in following.json()["data"]["items"]}

    await advance(client, admin_headers, issue["id"], "verified")
    notes = await client.get(f"{API}/notifications", headers=follower)
    assert any(n["issue_id"] == issue["id"] for n in notes.json()["data"]["items"])


@pytest.mark.asyncio
async def test_favourites(client, auth_headers):
    assert (await client.post(f"{API}/stations/BA/favourite", headers=auth_headers)).status_code == 200
    codes = (await client.get(f"{API}/me/favourites", headers=auth_headers)).json()["data"]["codes"]
    assert "BA" in codes
    await client.delete(f"{API}/stations/BA/favourite", headers=auth_headers)
    codes = (await client.get(f"{API}/me/favourites", headers=auth_headers)).json()["data"]["codes"]
    assert "BA" not in codes


@pytest.mark.asyncio
async def test_rating_only_after_fix_and_only_by_people_involved(client, bandra_station_id, admin_headers):
    reporter = await login(client, new_mobile())
    stranger = await login(client, new_mobile())
    issue = await create_issue(client, reporter, bandra_station_id, "Rating test broken bench seat")

    early = await client.post(f"{API}/issues/{issue['id']}/rating", headers=reporter, json={"rating": 5})
    assert early.status_code == 400

    await advance(client, admin_headers, issue["id"], "verified", "action_started", "completed")
    denied = await client.post(f"{API}/issues/{issue['id']}/rating", headers=stranger, json={"rating": 1})
    assert denied.status_code == 403

    ok = await client.post(f"{API}/issues/{issue['id']}/rating", headers=reporter, json={"rating": 4})
    assert ok.json()["data"] == {"average": 4.0, "count": 1}


@pytest.mark.asyncio
async def test_feed_filters_and_urgent_sort(client, bandra_station_id):
    reporter = await login(client, new_mobile())
    urgent = await create_issue(
        client, reporter, bandra_station_id, "Exposed live wire near stairs", "safety_security", True
    )
    res = await client.get(
        f"{API}/issues",
        params={"station_code": "BA", "category_code": "safety_security", "open_only": True, "sort": "urgent"},
    )
    items = res.json()["data"]["items"]
    assert items[0]["is_emergency"] is True
    assert urgent["id"] in {i["id"] for i in items}
    assert items[0]["sla_due_at"] is not None


@pytest.mark.asyncio
async def test_offensive_language_is_rejected(client, bandra_station_id):
    reporter = await login(client, new_mobile())
    res = await client.post(
        f"{API}/issues",
        headers=reporter,
        json={"description": "This fucking lift never works here", "station_id": bandra_station_id},
    )
    assert res.status_code == 400


@pytest.mark.asyncio
async def test_photo_metadata_is_stripped_and_proof_needs_staff(client, bandra_station_id, admin_headers):
    reporter = await login(client, new_mobile())
    issue = await create_issue(client, reporter, bandra_station_id, "Photo test cracked tile on floor")
    buffer = io.BytesIO()
    exif = Image.Exif()
    exif[0x010E] = "secret description"
    Image.new("RGB", (20, 20), "red").save(buffer, format="JPEG", exif=exif)
    files = {"file": ("a.jpg", buffer.getvalue(), "image/jpeg")}

    denied = await client.post(
        f"{API}/issues/{issue['id']}/photos", headers=reporter, files=files, params={"kind": "resolution"}
    )
    assert denied.status_code == 403
    ok = await client.post(f"{API}/issues/{issue['id']}/photos", headers=reporter, files=files)
    assert ok.status_code == 201

    from app.services.storage import storage_service

    assert b"secret description" not in storage_service.strip_metadata(buffer.getvalue(), "image/jpeg")

    proof = await client.post(
        f"{API}/issues/{issue['id']}/photos", headers=admin_headers, files=files, params={"kind": "resolution"}
    )
    assert proof.json()["data"]["kind"] == "resolution"


@pytest.mark.asyncio
async def test_internal_notes_stay_private(client, bandra_station_id, admin_headers):
    reporter = await login(client, new_mobile())
    issue = await create_issue(client, reporter, bandra_station_id, "Note test noisy announcement speaker")
    res = await client.post(
        f"{API}/admin/issues/{issue['id']}/notes", headers=admin_headers, json={"body": "Vendor called twice"}
    )
    assert res.status_code == 201

    staff_view = await client.get(f"{API}/admin/issues/{issue['id']}/detail", headers=admin_headers)
    assert any("Vendor called" in (e["remarks"] or "") for e in staff_view.json()["data"]["timeline"])

    public = await client.get(f"{API}/issues/{issue['id']}")
    assert not any("Vendor called" in (e["remarks"] or "") for e in public.json()["data"]["timeline"])

    denied = await client.get(f"{API}/admin/issues/{issue['id']}/detail", headers=reporter)
    assert denied.status_code == 403


@pytest.mark.asyncio
async def test_bulk_status_reports_what_it_skipped(client, bandra_station_id, admin_headers):
    reporter = await login(client, new_mobile())
    first = await create_issue(client, reporter, bandra_station_id, "Bulk test one, dirty bench")
    second = await create_issue(client, reporter, bandra_station_id, "Bulk test two, dirty wall")
    await advance(client, admin_headers, second["id"], "verified", "action_started")

    res = await client.post(
        f"{API}/admin/issues/bulk-status",
        headers=admin_headers,
        json={"issue_ids": [first["id"], second["id"]], "status": "verified", "remarks": "Checked on rounds"},
    )
    data = res.json()["data"]
    assert data["updated"] == [first["id"]]
    assert data["skipped"][0]["id"] == second["id"]


@pytest.mark.asyncio
async def test_merge_moves_backers_and_hides_duplicate(client, bandra_station_id, admin_headers):
    first_reporter = await login(client, new_mobile())
    second_reporter = await login(client, new_mobile())
    keep = await create_issue(client, first_reporter, bandra_station_id, "Merge test broken fan at gate")
    dupe = await create_issue(client, second_reporter, bandra_station_id, "Merge test fan broken at the gate")

    res = await client.post(
        f"{API}/admin/issues/{dupe['id']}/merge", headers=admin_headers, json={"target_id": keep["id"]}
    )
    assert res.status_code == 200
    assert res.json()["data"]["backers_added"] == 1

    assert (await client.get(f"{API}/issues/{dupe['id']}")).status_code == 404
    after = await client.get(f"{API}/issues/{keep['id']}")
    assert after.json()["data"]["issue"]["support_count"] == 2


@pytest.mark.asyncio
async def test_department_and_queue_filters(client, bandra_station_id, admin_headers):
    reporter = await login(client, new_mobile())
    issue = await create_issue(client, reporter, bandra_station_id, "Department test flickering platform light")
    res = await client.patch(
        f"{API}/admin/issues/{issue['id']}/department", headers=admin_headers, json={"department": "electrical"}
    )
    assert res.json()["data"]["department"] == "electrical"
    queue = await client.get(f"{API}/admin/issues", headers=admin_headers, params={"department": "electrical"})
    assert issue["id"] in {i["id"] for i in queue.json()["data"]["items"]}


@pytest.mark.asyncio
async def test_sla_sweep_escalates_overdue_once(client, bandra_station_id, admin_headers):
    from datetime import datetime, timedelta, timezone

    from app.db.session import async_session_factory
    from app.models.issue import Issue

    reporter = await login(client, new_mobile())
    issue = await create_issue(client, reporter, bandra_station_id, "SLA test open drain on platform")
    async with async_session_factory() as session:
        async with session.begin():
            row = await session.get(Issue, uuid.UUID(issue["id"]))
            row.created_at = datetime.now(timezone.utc) - timedelta(days=30)

    first = await client.post(f"{API}/admin/sla/sweep", headers=admin_headers)
    assert first.json()["data"]["escalated"] >= 1
    detail = await client.get(f"{API}/issues/{issue['id']}")
    assert detail.json()["data"]["issue"]["status"] == "forwarded_division"
    assert detail.json()["data"]["issue"]["overdue"] is True
    again = await client.post(f"{API}/admin/sla/sweep", headers=admin_headers)
    assert issue["id"] not in str(again.json())


@pytest.mark.asyncio
async def test_analytics_handover_audit(client, bandra_station_id, admin_headers):
    reporter = await login(client, new_mobile())
    await create_issue(client, reporter, bandra_station_id, "Analytics test damaged signboard")

    analytics = await client.get(f"{API}/admin/analytics", headers=admin_headers, params={"days": 7})
    assert analytics.status_code == 200
    data = analytics.json()["data"]
    assert len(data["trend"]) == 7
    assert data["total"] >= 1

    handover = await client.get(f"{API}/admin/handover", headers=admin_headers)
    assert handover.status_code == 200
    assert handover.json()["data"]["new_reports"]

    audit = await client.get(f"{API}/admin/audit", headers=admin_headers)
    assert audit.status_code == 200
    assert (await client.get(f"{API}/admin/audit", headers=reporter)).status_code == 403


@pytest.mark.asyncio
async def test_public_transparency_and_leaderboard(client, bandra_station_id):
    reporter = await login(client, new_mobile())
    await create_issue(client, reporter, bandra_station_id, "Transparency test missing dustbin")
    data = (await client.get(f"{API}/public/transparency")).json()["data"]
    assert data["total_reports"] >= 1
    assert any(s["code"] == "BA" for s in data["stations"])

    board = (await client.get(f"{API}/public/leaderboard")).json()["data"]
    assert board["passengers"]
    assert "mobile" not in str(board["passengers"][0])

    stats = (await client.get(f"{API}/stations/BA/stats")).json()["data"]
    assert stats["reports"] >= 1


@pytest.mark.asyncio
async def test_reputation_export_and_account_deletion(client, bandra_station_id):
    reporter = await login(client, new_mobile())
    issue = await create_issue(client, reporter, bandra_station_id, "Privacy test broken water tap")

    rep = (await client.get(f"{API}/me/reputation", headers=reporter)).json()["data"]
    assert rep["reports"] == 1
    assert rep["points"] == 10
    assert rep["badges"][0]["code"] == "first_report"

    export = (await client.get(f"{API}/me/export", headers=reporter)).json()["data"]
    assert export["reports"][0]["description"].startswith("Privacy test")

    assert (await client.post(f"{API}/me/delete", headers=reporter)).status_code == 200
    # The token no longer works, and the report stays without the name.
    assert (await client.get(f"{API}/me/reputation", headers=reporter)).status_code == 401
    kept = await client.get(f"{API}/issues/{issue['id']}")
    assert kept.json()["data"]["issue"]["creator"]["display_name"] == "Deleted user"


@pytest.mark.asyncio
async def test_repeat_abuser_is_locked(client, bandra_station_id, admin_headers):
    from app.core.config import settings

    abuser = await login(client, new_mobile())
    flagger = await login(client, new_mobile())
    locked = False
    for n in range(settings.abuse_lock_threshold):
        issue = await create_issue(client, abuser, bandra_station_id, f"Abuse test number {n} junk posting")
        await client.post(f"{API}/issues/{issue['id']}/flag", headers=flagger, json={"reason": "spam"})
        flags = (await client.get(f"{API}/admin/flags", headers=admin_headers)).json()["data"]["items"]
        flag = next(f for f in flags if f["issue"]["id"] == issue["id"])
        res = await client.post(
            f"{API}/admin/flags/{flag['id']}/resolve", headers=admin_headers, json={"action": "hide"}
        )
        locked = res.json()["data"]["author_locked"]
    assert locked is True
    assert (await client.get(f"{API}/me/reputation", headers=abuser)).status_code == 403

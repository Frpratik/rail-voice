import pytest
from httpx import AsyncClient

API = "/api/v1"


@pytest.mark.asyncio
async def test_csat_feedback_submission(client: AsyncClient, bandra_station_id: str):
    anon = await client.post(f"{API}/auth/anonymous")
    headers = {"X-Anonymous-Session": anon.json()["data"]["anonymous_session_id"]}

    # 1. Create Issue
    create_res = await client.post(
        f"{API}/issues",
        headers=headers,
        json={
            "title": "Cleanliness issue for CSAT test",
            "description": "Water bottle and trash on platform 1 Bandra station",
            "station_id": bandra_station_id,
            "force_create": True,
            "divergence_reason": "CSAT feedback unit test submission",
        },
    )
    assert create_res.status_code == 201
    issue_id = create_res.json()["data"]["issue"]["id"]

    # 2. Submit 5-Star Rating Feedback
    feedback_payload = {
        "rating": 5,
        "comments": "Staff cleaned the area quickly. Excellent response!",
        "is_reopened": False,
    }
    fb_res = await client.post(f"{API}/issues/{issue_id}/feedback", json=feedback_payload)
    assert fb_res.status_code == 200
    fb_data = fb_res.json()["data"]
    assert fb_data["rating"] == 5
    assert fb_data["is_reopened"] is False

    # 3. Fetch Submitted Feedback
    get_fb = await client.get(f"{API}/issues/{issue_id}/feedback")
    assert get_fb.status_code == 200
    assert get_fb.json()["data"]["rating"] == 5


@pytest.mark.asyncio
async def test_csat_reopen_grievance(client: AsyncClient, bandra_station_id: str):
    anon = await client.post(f"{API}/auth/anonymous")
    headers = {"X-Anonymous-Session": anon.json()["data"]["anonymous_session_id"]}

    # 1. Create Issue
    create_res = await client.post(
        f"{API}/issues",
        headers=headers,
        json={
            "title": "Escalator fault for CSAT reopen test",
            "description": "Foot overbridge escalator at Bandra station platform 2 broken",
            "station_id": bandra_station_id,
            "force_create": True,
            "divergence_reason": "CSAT reopen unit test submission",
        },
    )
    assert create_res.status_code == 201
    issue_id = create_res.json()["data"]["issue"]["id"]

    # 2. Submit Low Rating & Reopen Request
    reopen_payload = {
        "rating": 1,
        "comments": "Ticket marked resolved but escalator is still stopped!",
        "is_reopened": True,
        "reopen_reason": "Escalator is still non-functional and dangerous",
    }
    reopen_res = await client.post(f"{API}/issues/{issue_id}/feedback", json=reopen_payload)
    assert reopen_res.status_code == 200
    data = reopen_res.json()["data"]
    assert data["is_reopened"] is True
    assert data["new_status"] == "work_in_progress"
    assert data["reopen_count"] >= 1
    assert data["priority_score"] >= 25.0

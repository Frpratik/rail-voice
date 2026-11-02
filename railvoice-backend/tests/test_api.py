import pytest
from httpx import ASGITransport, AsyncClient

from app.main import app

API = "/api/v1"


@pytest.mark.asyncio
async def test_health():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        response = await client.get("/health")
    assert response.status_code == 200
    assert response.json()["status"] == "ok"


@pytest.mark.asyncio
async def test_list_stations(client):
    response = await client.get(f"{API}/stations")
    assert response.status_code == 200
    data = response.json()["data"]
    assert isinstance(data, list)
    assert len(data) >= 29
    assert "code" in data[0]
    assert "name" in data[0]


@pytest.mark.asyncio
async def test_report_support_and_mine_flow(client, auth_headers, bandra_station_id):
    create1 = await client.post(
        f"{API}/issues",
        headers=auth_headers,
        json={
            "description": "There should be a dustbin near Platform 2 bridge at Bandra.",
            "station_id": bandra_station_id,
            "title": "Dustbin needed",
        },
    )
    assert create1.status_code == 201
    issue_id = create1.json()["data"]["issue"]["id"]

    # Creator already supports their own issue, so a second support is a conflict.
    again = await client.post(f"{API}/issues/{issue_id}/support", headers=auth_headers)
    assert again.status_code == 409

    mine = await client.get(f"{API}/issues/mine", headers=auth_headers)
    assert mine.status_code == 200
    mine_ids = {item["id"] for item in mine.json()["data"]["items"]}
    assert create1.json()["data"]["issue"]["id"] in mine_ids


@pytest.mark.asyncio
async def test_anonymous_session_can_submit_issue(
    client, anonymous_headers, bandra_station_id
):
    payload = {
        "description": "Anonymous passengers can report without creating an account",
        "station_id": bandra_station_id,
    }
    response = await client.post(f"{API}/issues", headers=anonymous_headers, json=payload)
    assert response.status_code == 201

    no_identity = await client.post(f"{API}/issues", json=payload)
    assert no_identity.status_code == 401

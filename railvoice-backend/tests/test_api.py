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
async def test_duplicate_detection_flow(client, auth_headers, bandra_station_id):
    description = "There should be a dustbin near Platform 2 bridge at Bandra."
    create1 = await client.post(
        f"{API}/issues",
        headers=auth_headers,
        json={
            "description": description,
            "station_id": bandra_station_id,
            "title": "Dustbin needed",
            "force_create": True,
            "divergence_reason": "Initial seed issue for duplicate test",
        },
    )
    assert create1.status_code == 201

    check = await client.post(
        f"{API}/issues/check-duplicates",
        headers=auth_headers,
        json={
            "description": "Garbage bins are missing beside the foot over bridge on Bandra Platform 2",
            "station_id": bandra_station_id,
        },
    )
    assert check.status_code == 200
    result = check.json()["data"]
    assert result["has_similar"] is True
    assert len(result["similar_issues"]) >= 1
    assert result["similar_issues"][0]["similarity"] >= 0.45

    dup_create = await client.post(
        f"{API}/issues",
        headers=auth_headers,
        json={
            "description": "Garbage bins are missing beside the foot over bridge on Bandra Platform 2",
            "station_id": bandra_station_id,
        },
    )
    assert dup_create.status_code == 409
    assert dup_create.json()["detail"]["code"] == "DUPLICATE_FOUND"

    support = await client.post(
        f"{API}/issues/{result['similar_issues'][0]['id']}/support",
        headers=auth_headers,
    )
    assert support.status_code == 200
    assert support.json()["data"]["support_count"] >= 1

    mine = await client.get(f"{API}/issues/mine", headers=auth_headers)
    assert mine.status_code == 200
    mine_ids = {item["id"] for item in mine.json()["data"]["items"]}
    assert create1.json()["data"]["issue"]["id"] in mine_ids


@pytest.mark.asyncio
async def test_anonymous_user_cannot_submit_issue(
    client, anonymous_headers, bandra_station_id
):
    response = await client.post(
        f"{API}/issues",
        headers=anonymous_headers,
        json={
            "description": "Anonymous passengers must sign in before submitting this report",
            "station_id": bandra_station_id,
            "force_create": True,
            "divergence_reason": "Authentication requirement test",
        },
    )
    assert response.status_code == 401

import pytest
from httpx import AsyncClient

API = "/api/v1"


@pytest.mark.asyncio
async def test_idempotency_key_prevents_duplicate_processing(
    client: AsyncClient, anonymous_headers: dict, bandra_station_id: str
):
    headers = {**anonymous_headers, "Idempotency-Key": "test-key-12345"}
    payload = {
        "description": "Idempotency test issue description with sufficient length",
        "station_id": bandra_station_id,
        "title": "Idempotency Test",
    }

    # First request
    res1 = await client.post(f"{API}/issues", headers=headers, json=payload)
    assert res1.status_code == 201
    issue_id1 = res1.json()["data"]["issue"]["id"]

    # Second request with SAME Idempotency-Key
    res2 = await client.post(f"{API}/issues", headers=headers, json=payload)
    assert res2.status_code == 201
    assert res2.headers.get("X-Idempotency-Hit") == "true"
    issue_id2 = res2.json()["data"]["issue"]["id"]

    # Should return cached response with identical issue ID
    assert issue_id1 == issue_id2

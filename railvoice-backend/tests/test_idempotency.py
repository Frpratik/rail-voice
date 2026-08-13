import pytest
from httpx import AsyncClient

API = "/api/v1"


import uuid

@pytest.mark.asyncio
async def test_idempotency_key_prevents_duplicate_processing(
    client: AsyncClient, auth_headers: dict, bandra_station_id: str
):
    uid = uuid.uuid4()
    key = f"test-key-{uid}"
    headers = {**auth_headers, "Idempotency-Key": key}
    payload = {
        "description": f"Unique idempotency description {uid} with sufficient length to bypass duplicate filter",
        "station_id": bandra_station_id,
        "title": f"Idempotency Test {uid}",
        "force_create": True,
        "divergence_reason": "Testing idempotency cache key response bypass",
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

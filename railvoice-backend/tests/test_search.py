import pytest
from httpx import AsyncClient

API = "/api/v1"


@pytest.mark.asyncio
async def test_hybrid_search_finds_issue(
    client: AsyncClient,
    anonymous_headers: dict,
    bandra_station_id: str,
):
    description = "Broken lift near ticket counter at Bandra station west side"
    create = await client.post(
        f"{API}/issues",
        headers=anonymous_headers,
        json={
            "description": description,
            "station_id": bandra_station_id,
            "force_create": True,
            "divergence_reason": "Search integration test seed issue",
        },
    )
    assert create.status_code == 201

    search = await client.get(f"{API}/search?q=broken+lift+Bandra")
    assert search.status_code == 200
    results = search.json()["data"]["results"]
    assert len(results) >= 1
    assert results[0]["match_type"] in {"semantic", "keyword", "hybrid"}


@pytest.mark.asyncio
async def test_semantic_search_endpoint(client: AsyncClient, bandra_station_id: str):
    response = await client.post(
        f"{API}/search/semantic",
        json={
            "query": "missing dustbin platform bridge",
            "station_id": bandra_station_id,
            "limit": 5,
        },
    )
    assert response.status_code == 200
    assert "results" in response.json()["data"]

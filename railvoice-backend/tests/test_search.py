import pytest
from httpx import AsyncClient

API = "/api/v1"


@pytest.mark.asyncio
async def test_text_search_finds_issue(
    client: AsyncClient,
    auth_headers: dict,
    bandra_station_id: str,
):
    description = "Broken lift near ticket counter at Bandra station west side"
    create = await client.post(
        f"{API}/issues",
        headers=auth_headers,
        json={
            "description": description,
            "station_id": bandra_station_id,
        },
    )
    assert create.status_code == 201

    search = await client.get(f"{API}/search?q=broken+lift+Bandra")
    assert search.status_code == 200
    results = search.json()["data"]["results"]
    assert len(results) >= 1
    assert results[0]["match_type"] in {"text"}


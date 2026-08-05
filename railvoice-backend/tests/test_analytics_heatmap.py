import pytest
from httpx import AsyncClient

@pytest.mark.asyncio
async def test_get_station_heatmap(client: AsyncClient):
    response = await client.get("/api/v1/station-heatmap")
    assert response.status_code == 200
    data = response.json()
    assert data["type"] == "FeatureCollection"
    assert "features" in data
    assert isinstance(data["features"], list)

import pytest
from httpx import AsyncClient

API = "/api/v1"

@pytest.mark.asyncio
async def test_get_dispatch_roster(client: AsyncClient):
    response = await client.get(f"{API}/admin/dispatch/roster")
    assert response.status_code == 200
    data = response.json()["data"]
    assert "total_staff" in data
    assert "available_count" in data
    assert "staff_list" in data
    assert data["total_staff"] > 0

@pytest.mark.asyncio
async def test_get_dispatch_recommendations(client: AsyncClient):
    response = await client.get(f"{API}/admin/dispatch/recommendations")
    assert response.status_code == 200
    data = response.json()["data"]
    assert isinstance(data, list)

@pytest.mark.asyncio
async def test_auto_assign_dispatch(client: AsyncClient):
    response = await client.post(f"{API}/admin/dispatch/auto-assign")
    assert response.status_code == 200
    data = response.json()["data"]
    assert "dispatched_count" in data
    assert "assignments" in data

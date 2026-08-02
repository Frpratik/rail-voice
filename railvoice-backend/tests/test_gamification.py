import pytest
from httpx import AsyncClient

API = "/api/v1"


@pytest.mark.asyncio
async def test_get_user_leaderboard(client: AsyncClient):
    res = await client.get(f"{API}/gamification/leaderboard/users")
    assert res.status_code == 200
    assert "data" in res.json()


@pytest.mark.asyncio
async def test_get_station_leaderboard(client: AsyncClient):
    res = await client.get(f"{API}/gamification/leaderboard/stations")
    assert res.status_code == 200
    assert "data" in res.json()


@pytest.mark.asyncio
async def test_get_my_reputation(client: AsyncClient, auth_headers: dict):
    res = await client.get(f"{API}/gamification/profile/me", headers=auth_headers)
    assert res.status_code == 200
    data = res.json()["data"]

    assert "points" in data
    assert "tier" in data
    assert "badge_slugs" in data

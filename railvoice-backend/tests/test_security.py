import pytest
from httpx import AsyncClient

API = "/api/v1"


@pytest.mark.asyncio
async def test_issue_detail_not_found(client: AsyncClient):
    response = await client.get(
        f"{API}/issues/00000000-0000-0000-0000-000000000099"
    )
    assert response.status_code == 404


@pytest.mark.asyncio
async def test_create_issue_validation(client: AsyncClient, auth_headers: dict):
    response = await client.post(
        f"{API}/issues",
        headers=auth_headers,
        json={"description": "short", "station_id": "00000000-0000-0000-0000-000000000001"},
    )
    assert response.status_code == 422


@pytest.mark.asyncio
async def test_passenger_cannot_access_admin(client: AsyncClient, auth_headers: dict):
    response = await client.get(f"{API}/admin/dashboard", headers=auth_headers)
    assert response.status_code == 403


@pytest.mark.asyncio
async def test_support_requires_session_or_auth(client: AsyncClient, bandra_station_id: str):
    response = await client.post(f"{API}/issues/00000000-0000-0000-0000-000000000001/support")
    assert response.status_code in {400, 401, 404}

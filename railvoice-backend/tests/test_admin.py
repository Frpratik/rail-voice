import pytest
from httpx import AsyncClient

API = "/api/v1"


@pytest.mark.asyncio
async def test_admin_dashboard_requires_auth(client: AsyncClient):
    response = await client.get(f"{API}/admin/dashboard")
    assert response.status_code == 401


@pytest.mark.asyncio
async def test_admin_dashboard_for_official(client: AsyncClient, admin_headers: dict):
    response = await client.get(f"{API}/admin/dashboard", headers=admin_headers)
    assert response.status_code == 200
    data = response.json()["data"]
    assert "kpis" in data
    assert "open_issues" in data["kpis"]


@pytest.mark.asyncio
async def test_admin_issue_status_update(
    client: AsyncClient,
    admin_headers: dict,
    anonymous_headers: dict,
    bandra_station_id: str,
):
    create = await client.post(
        f"{API}/issues",
        headers=anonymous_headers,
        json={
            "description": "Water leakage from ceiling at Bandra platform 3 waiting area",
            "station_id": bandra_station_id,
            "force_create": True,
            "divergence_reason": "Admin lifecycle integration test",
        },
    )
    assert create.status_code == 201
    issue_id = create.json()["data"]["issue"]["id"]

    update = await client.patch(
        f"{API}/admin/issues/{issue_id}/status",
        headers=admin_headers,
        json={
            "status": "verified",
            "remarks": "Verified after initial review by station moderator",
        },
    )
    assert update.status_code == 200
    assert update.json()["data"]["issue"]["status"] == "verified"


@pytest.mark.asyncio
async def test_daily_ai_summary(client: AsyncClient, admin_headers: dict):
    response = await client.get(
        f"{API}/admin/analytics/ai-insights/daily-summary",
        headers=admin_headers,
    )
    assert response.status_code == 200
    data = response.json()["data"]
    assert "narrative" in data
    assert "stats" in data

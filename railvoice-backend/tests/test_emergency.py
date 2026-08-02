import pytest
from httpx import AsyncClient

API = "/api/v1"


@pytest.mark.asyncio
async def test_list_active_emergency_alerts(client: AsyncClient):
    res = await client.get(f"{API}/emergency/alerts/active")
    assert res.status_code == 200
    assert "data" in res.json()


@pytest.mark.asyncio
async def test_create_and_deactivate_emergency_alert(
    client: AsyncClient, admin_headers: dict
):
    payload = {
        "station_id": None,
        "severity": "critical",
        "title": "Platform Overhead Wire Hazard",
        "message": "Overhead traction wire snapped on Western Railway corridor. Commuters advised to stay clear.",
        "duration_hours": 4,
    }

    # 1. Create Emergency Alert
    res = await client.post(f"{API}/emergency/alerts", headers=admin_headers, json=payload)
    assert res.status_code == 201
    alert_data = res.json()["data"]
    alert_id = alert_data["id"]

    assert alert_data["title"] == "Platform Overhead Wire Hazard"
    assert alert_data["severity"] == "critical"
    assert alert_data["is_active"] is True

    # 2. Verify active alerts API returns the newly created alert
    active_res = await client.get(f"{API}/emergency/alerts/active")
    assert active_res.status_code == 200
    active_list = active_res.json()["data"]
    assert any(a["id"] == alert_id for a in active_list)

    # 3. Deactivate Alert
    deact_res = await client.patch(f"{API}/emergency/alerts/{alert_id}/deactivate", headers=admin_headers)
    assert deact_res.status_code == 200
    assert deact_res.json()["data"]["is_active"] is False

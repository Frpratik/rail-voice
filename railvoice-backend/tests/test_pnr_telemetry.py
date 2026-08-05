import pytest
from httpx import AsyncClient

API = "/api/v1"


@pytest.mark.asyncio
async def test_pnr_lookup(client: AsyncClient):
    res = await client.post(f"{API}/telemetry/pnr-lookup", json={"pnr_number": "8204910245"})
    assert res.status_code == 200
    data = res.json()["data"]
    assert data["pnr_number"] == "8204910245"
    assert data["train_number"] in ["12951", "12953", "19015", "12925"]
    assert data["obhs_assigned"] is True


@pytest.mark.asyncio
async def test_live_train_status(client: AsyncClient):
    res = await client.get(f"{API}/telemetry/train-status/12951")
    assert res.status_code == 200
    data = res.json()["data"]
    assert data["train_number"] == "12951"
    assert data["is_running_live"] is True


@pytest.mark.asyncio
async def test_issue_creation_with_pnr_telemetry(client: AsyncClient, bandra_station_id: str):
    anon = await client.post(f"{API}/auth/anonymous")
    headers = {"X-Anonymous-Session": anon.json()["data"]["anonymous_session_id"]}

    create_res = await client.post(
        f"{API}/issues",
        headers=headers,
        json={
            "title": "Dirty Coach B4 Washroom on Mumbai Rajdhani",
            "description": "Washroom near berth 22 in coach B4 requires urgent OBHS cleaning",
            "station_id": bandra_station_id,
            "pnr_number": "8204910245",
            "train_number": "12951",
            "coach_number": "B4",
            "berth_number": "22",
            "upcoming_station_code": "ST",
            "force_create": True,
            "divergence_reason": "PNR moving train grievance unit test",
        },
    )
    assert create_res.status_code == 201
    issue_data = create_res.json()["data"]["issue"]
    assert issue_data["location"]["pnr_number"] == "8204910245"
    assert issue_data["location"]["coach_number"] == "B4"
    assert issue_data["location"]["berth_number"] == "22"
    assert issue_data["location"]["upcoming_station_code"] == "ST"

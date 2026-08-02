import pytest
from httpx import AsyncClient

API = "/api/v1"


@pytest.mark.asyncio
async def test_whatsapp_webhook_verification(client: AsyncClient):
    res = await client.get(
        f"{API}/whatsapp/webhook",
        params={
            "hub.mode": "subscribe",
            "hub.verify_token": "railvoice_whatsapp_token_2026",
            "hub.challenge": "CHALLENGE_123",
        },
    )
    assert res.status_code == 200
    assert res.text == "CHALLENGE_123"


@pytest.mark.asyncio
async def test_whatsapp_simulate_inbound_report(client: AsyncClient):
    payload = {
        "sender_phone": "+919876543210",
        "message": "Water leak issue at Bandra station platform 1",
    }
    res = await client.post(f"{API}/whatsapp/simulate", json=payload)
    assert res.status_code == 200
    data = res.json()["data"]

    assert data["issue_id"] is not None
    assert "Grievance Registered" in data["reply"]
    assert "BDTS" in data["reply"] or "Bandra" in data["reply"]


@pytest.mark.asyncio
async def test_whatsapp_webhook_post_form_data(client: AsyncClient):
    form_data = {
        "From": "+919988776655",
        "Body": "Escalator broken at Andheri station",
    }
    res = await client.post(f"{API}/whatsapp/webhook", data=form_data)
    assert res.status_code == 200
    assert "Grievance Registered" in res.text

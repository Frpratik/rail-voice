import pytest
from httpx import AsyncClient

pytestmark = pytest.mark.integration

API = "/api/v1"


@pytest.mark.asyncio
async def test_otp_request_and_verify(client: AsyncClient):
    mobile = "+919111111111"
    req = await client.post(f"{API}/auth/otp/request", json={"mobile": mobile})
    assert req.status_code == 200
    assert "expires_in_seconds" in req.json()["data"]

    verify = await client.post(
        f"{API}/auth/otp/verify",
        json={"mobile": mobile, "otp": "123456"},
    )
    assert verify.status_code == 200
    data = verify.json()["data"]
    assert "access_token" in data
    assert data["user"]["is_verified"] is True


@pytest.mark.asyncio
async def test_anonymous_session(client: AsyncClient):
    response = await client.post(f"{API}/auth/anonymous")
    assert response.status_code == 200
    body = response.json()["data"]
    assert "anonymous_session_id" in body
    assert body["limits"]["issues_per_24h"] == 3


@pytest.mark.asyncio
async def test_invalid_otp_rejected(client: AsyncClient):
    mobile = "+919222222222"
    await client.post(f"{API}/auth/otp/request", json={"mobile": mobile})
    response = await client.post(
        f"{API}/auth/otp/verify",
        json={"mobile": mobile, "otp": "000000"},
    )
    assert response.status_code == 400


@pytest.mark.asyncio
async def test_google_mock_login(client: AsyncClient):
    response = await client.post(
        f"{API}/auth/google",
        json={
            "id_token": "mock-token",
            "email": "phase2.google@railvoice.local",
            "name": "Phase2 Google",
            "google_id": "mock-phase2-google",
        },
    )
    assert response.status_code == 200
    data = response.json()["data"]
    assert data["user"]["email"] == "phase2.google@railvoice.local"
    assert "access_token" in data


@pytest.mark.asyncio
async def test_otp_request_includes_mock_otp_in_mock_mode(client: AsyncClient):
    response = await client.post(f"{API}/auth/otp/request", json={"mobile": "+919333333333"})
    assert response.status_code == 200
    assert response.json()["data"].get("mock_otp") == "123456"


@pytest.mark.asyncio
async def test_logout_requires_auth(client: AsyncClient):
    response = await client.post(f"{API}/auth/logout")
    assert response.status_code == 401

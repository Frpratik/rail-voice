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


import uuid

@pytest.mark.asyncio
async def test_invalid_otp_rejected(client: AsyncClient):
    mobile = f"+919{uuid.uuid4().int % 1000000000:09d}"
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
    assert data["user"]["display_name"] == "Phase2 Google"
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


@pytest.mark.asyncio
async def test_refresh_rotation_and_reuse_detection(client: AsyncClient):
    mobile = "+919876500001"
    await client.post(f"{API}/auth/otp/request", json={"mobile": mobile})
    verify = await client.post(f"{API}/auth/otp/verify", json={"mobile": mobile, "otp": "123456"})
    old_refresh = verify.json()["data"]["refresh_token"]

    rotated = await client.post(f"{API}/auth/refresh", json={"refresh_token": old_refresh})
    assert rotated.status_code == 200
    new_refresh = rotated.json()["data"]["refresh_token"]
    assert new_refresh != old_refresh

    reuse = await client.post(f"{API}/auth/refresh", json={"refresh_token": old_refresh})
    assert reuse.status_code == 401
    # Reuse revokes the whole family, including the newest token.
    family = await client.post(f"{API}/auth/refresh", json={"refresh_token": new_refresh})
    assert family.status_code == 401

"""Shared pytest fixtures for RailVoice integration tests."""

from __future__ import annotations

import pytest
from httpx import ASGITransport, AsyncClient

from app.core.config import settings
from app.main import app

API = "/api/v1"
ADMIN_MOBILE = "+919999999999"
MOCK_OTP = "123456"


@pytest.fixture(autouse=True)
def disable_rate_limiting():
    settings.rate_limit_enabled = False
    settings.google_oauth_mock_mode = True
    yield
    settings.rate_limit_enabled = False
    settings.google_oauth_mock_mode = True


@pytest.fixture
async def client():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        yield ac


@pytest.fixture
async def anonymous_headers(client: AsyncClient) -> dict[str, str]:
    response = await client.post(f"{API}/auth/anonymous")
    assert response.status_code == 200
    session_id = response.json()["data"]["anonymous_session_id"]
    return {"X-Anonymous-Session": session_id}


@pytest.fixture
async def auth_headers(client: AsyncClient) -> dict[str, str]:
    mobile = "+919876543210"
    await client.post(f"{API}/auth/otp/request", json={"mobile": mobile})
    response = await client.post(
        f"{API}/auth/otp/verify",
        json={"mobile": mobile, "otp": MOCK_OTP},
    )
    assert response.status_code == 200
    token = response.json()["data"]["access_token"]
    return {"Authorization": f"Bearer {token}"}


@pytest.fixture
async def admin_headers(client: AsyncClient) -> dict[str, str]:
    await client.post(f"{API}/auth/otp/request", json={"mobile": ADMIN_MOBILE})
    response = await client.post(
        f"{API}/auth/otp/verify",
        json={"mobile": ADMIN_MOBILE, "otp": MOCK_OTP},
    )
    assert response.status_code == 200
    token = response.json()["data"]["access_token"]
    return {"Authorization": f"Bearer {token}"}


@pytest.fixture
async def bandra_station_id(client: AsyncClient) -> str:
    response = await client.get(f"{API}/stations?search=Bandra")
    assert response.status_code == 200
    stations = response.json()["data"]
    assert stations, "Bandra station must exist in seed data"
    return stations[0]["id"]


@pytest.fixture(scope="session")
def ai_duplicate_pairs():
    import json
    from pathlib import Path

    path = Path(__file__).parent / "fixtures" / "ai_duplicate_pairs.json"
    return json.loads(path.read_text(encoding="utf-8"))

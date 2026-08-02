"""Phase 2 production-trust unit tests (no DB required)."""

from __future__ import annotations

import pytest

from app.core.config import Settings
from app.core.rate_limit import MemoryRateLimitBackend
from app.services.sms.provider import ConsoleSmsProvider, get_sms_provider


def test_production_rejects_mocks():
    settings = Settings(
        app_env="production",
        secret_key="x" * 40,
        otp_mock_mode=True,
        google_oauth_mock_mode=True,
        cors_origins="https://example.com",
        redis_url="redis://localhost:6379/0",
        sms_provider="twilio",
        twilio_account_sid="ACxxx",
        twilio_auth_token="tok",
        twilio_from_number="+15551234567",
        google_client_id="client.apps.googleusercontent.com",
    )
    errors = settings.validate_for_runtime()
    assert any("OTP_MOCK_MODE" in e for e in errors)
    assert any("GOOGLE_OAUTH_MOCK_MODE" in e for e in errors)


def test_production_requires_sms_provider_and_redis():
    settings = Settings(
        app_env="production",
        secret_key="x" * 40,
        otp_mock_mode=False,
        google_oauth_mock_mode=False,
        cors_origins="https://example.com",
        redis_url="",
        sms_provider="console",
        google_auth_enabled=True,
        google_client_id="client.apps.googleusercontent.com",
        rate_limit_require_redis_in_production=True,
    )
    errors = settings.validate_for_runtime()
    assert any("SMS_PROVIDER=console" in e for e in errors)
    assert any("REDIS_URL" in e for e in errors)


def test_production_ok_with_twilio():
    settings = Settings(
        app_env="production",
        secret_key="x" * 40,
        otp_mock_mode=False,
        google_oauth_mock_mode=False,
        cors_origins="https://example.com",
        redis_url="redis://localhost:6379/0",
        sms_provider="twilio",
        twilio_account_sid="ACxxx",
        twilio_auth_token="tok",
        twilio_from_number="+15551234567",
        google_client_id="client.apps.googleusercontent.com",
        rate_limit_require_redis_in_production=True,
    )
    assert settings.validate_for_runtime() == []


def test_memory_rate_limit_blocks():
    backend = MemoryRateLimitBackend()
    for _ in range(3):
        allowed, _, _, _ = backend.hit("t", limit=3, window_seconds=60)
        assert allowed
    allowed, limit, remaining, retry = backend.hit("t", limit=3, window_seconds=60)
    assert not allowed
    assert limit == 3
    assert remaining == 0
    assert retry >= 1


@pytest.mark.asyncio
async def test_console_sms_provider_send():
    provider = ConsoleSmsProvider()
    await provider.send_otp("+919876543210", "654321")


def test_get_sms_provider_mock_uses_console(monkeypatch):
    from app.core import config

    monkeypatch.setattr(config.settings, "otp_mock_mode", True)
    assert isinstance(get_sms_provider(), ConsoleSmsProvider)

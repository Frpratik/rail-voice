"""Pluggable SMS providers for OTP delivery."""

from __future__ import annotations

import logging
from typing import Protocol

import httpx

from app.core.config import settings

logger = logging.getLogger(__name__)


class SmsProvider(Protocol):
    async def send_otp(self, mobile: str, otp: str) -> None: ...


class ConsoleSmsProvider:
    """Local/CI provider — logs OTP; never use as sole path in production."""

    async def send_otp(self, mobile: str, otp: str) -> None:
        logger.warning("ConsoleSmsProvider OTP for %s: %s", mobile[-4:].rjust(len(mobile), "*"), otp)


class TwilioSmsProvider:
    async def send_otp(self, mobile: str, otp: str) -> None:
        sid = settings.twilio_account_sid
        token = settings.twilio_auth_token
        from_number = settings.twilio_from_number
        if not (sid and token and from_number):
            raise RuntimeError("Twilio is not configured")

        url = f"https://api.twilio.com/2010-04-01/Accounts/{sid}/Messages.json"
        body = (
            f"Your RailVoice verification code is {otp}. "
            f"Valid for {max(1, settings.otp_ttl_seconds // 60)} minutes."
        )
        async with httpx.AsyncClient(timeout=15.0) as client:
            response = await client.post(
                url,
                data={"To": mobile, "From": from_number, "Body": body},
                auth=(sid, token),
            )
            if response.status_code >= 400:
                logger.error("Twilio SMS failed: %s %s", response.status_code, response.text[:300])
                raise RuntimeError("SMS send failed")


class Msg91SmsProvider:
    async def send_otp(self, mobile: str, otp: str) -> None:
        if not (settings.msg91_auth_key and settings.msg91_template_id):
            raise RuntimeError("MSG91 is not configured")

        digits = mobile.lstrip("+")
        url = "https://control.msg91.com/api/v5/flow/"
        payload = {
            "template_id": settings.msg91_template_id,
            "short_url": "0",
            "recipients": [{"mobiles": digits, "otp": otp}],
        }
        headers = {
            "authkey": settings.msg91_auth_key,
            "Content-Type": "application/json",
            "accept": "application/json",
        }
        async with httpx.AsyncClient(timeout=15.0) as client:
            response = await client.post(url, json=payload, headers=headers)
            if response.status_code >= 400:
                logger.error("MSG91 SMS failed: %s %s", response.status_code, response.text[:300])
                raise RuntimeError("SMS send failed")


def get_sms_provider() -> SmsProvider:
    if settings.otp_mock_mode:
        return ConsoleSmsProvider()

    name = settings.sms_provider.lower().strip()
    if name == "twilio":
        return TwilioSmsProvider()
    if name == "msg91":
        return Msg91SmsProvider()
    return ConsoleSmsProvider()

from __future__ import annotations

import logging
import re
from typing import Any

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.models.location import Station
from app.models.user import User
from app.schemas.common import IssueCreateRequest
from app.services.issue_service import issue_service

logger = logging.getLogger(__name__)

STATION_KEYWORD_MAP = {
    "bandra": "BA",
    "ba": "BA",
    "bdts": "BA",
    "andheri": "ADH",
    "adh": "ADH",
    "borivali": "BVI",
    "bvi": "BVI",
    "dadar": "DDR",
    "ddr": "DDR",
    "virar": "VR",
    "vr": "VR",
    "churchgate": "CCG",
    "ccg": "CCG",
    "mumbai central": "BCT",
    "bct": "BCT",
}


class WhatsAppBotService:
    async def process_inbound_message(
        self,
        *,
        sender_phone: str,
        text: str,
        media_urls: list[str] | None = None,
        location: dict[str, float] | None = None,
        db: AsyncSession,
    ) -> dict[str, Any]:
        """Process inbound WhatsApp message, extract station/issue details, and create issue."""
        cleaned_text = (text or "").strip()
        if not cleaned_text and not media_urls:
            return {
                "reply": "🚆 *RailVoice Bot*\n\nPlease describe the issue or send a photo with your message (e.g. 'Cleanliness issue at Bandra station platform 1').",
                "issue_id": None,
            }

        # 1. Detect Station Code from text keywords or fallback to first available station
        detected_station_code = None
        lower_text = cleaned_text.lower()
        for kw, code in STATION_KEYWORD_MAP.items():
            if kw in lower_text:
                detected_station_code = code
                break

        station = None
        if detected_station_code:
            station = await db.scalar(select(Station).where(Station.code == detected_station_code))
        if not station:
            station = await db.scalar(select(Station).limit(1))

        if not station:
            return {
                "reply": "❌ *Error:* No active railway station found in database.",
                "issue_id": None,
            }

        # 2. Get or create WhatsApp system user reporter
        from app.core.security import hash_value

        m_hash = hash_value(sender_phone)
        reporter = await db.scalar(select(User).where(User.mobile_hash == m_hash))
        if not reporter:
            reporter = User(
                display_name=f"WhatsApp User ({sender_phone[-4:]})",
                mobile_hash=m_hash,
                is_active=True,
            )
            db.add(reporter)
            await db.flush()

        # 3. Formulate Issue Creation Request
        title_prefix = "WhatsApp Report: "
        short_title = (cleaned_text[:50] + "...") if len(cleaned_text) > 50 else cleaned_text
        if not short_title:
            short_title = "Photo report via WhatsApp"

        description = (
            f"{cleaned_text}\n\n[Reported via WhatsApp from {sender_phone}]"
            if cleaned_text
            else f"Photo report received via WhatsApp from {sender_phone}"
        )

        create_req = IssueCreateRequest(
            title=f"{title_prefix}{short_title}",
            description=description,
            station_id=station.id,
            category_id=None,
            coach_number=None,
            train_number=None,
            pnr_number=None,
            latitude=location.get("latitude") if location else None,
            longitude=location.get("longitude") if location else None,
        )

        # 4. Create Issue in DB
        issue = await issue_service.create_issue(
            db,
            creator=reporter,
            station_id=station.id,
            description=description,
            title=f"{title_prefix}{short_title}",
            latitude=location.get("latitude") if location else None,
            longitude=location.get("longitude") if location else None,
            force_create=True,
            divergence_reason="Direct WhatsApp report submission",
        )

        # 5. Format WhatsApp Reply Text
        track_url = f"{settings.public_base_url.rstrip('/')}/issues/{issue.id}"
        reply_text = (
            f"🚆 *RailVoice Grievance Registered*\n"
            f"---------------------------------\n"
            f"📍 *Station:* {station.name} ({station.code})\n"
            f"📋 *Issue Code:* `{issue.issue_number}`\n"
            f"⚡ *Status:* Submitted (Forwarded to Station Manager)\n\n"
            f"Track live resolution status:\n{track_url}\n\n"
            f"Thank you for helping keep Indian Railways clean & safe!"
        )

        return {
            "reply": reply_text,
            "issue_id": str(issue.id),
            "issue_code": issue.issue_number,
            "station_code": station.code,
        }


whatsapp_bot_service = WhatsAppBotService()

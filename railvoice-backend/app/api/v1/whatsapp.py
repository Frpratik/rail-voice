from __future__ import annotations

from typing import Annotated, Any

from fastapi import APIRouter, Depends, HTTPException, Query, Request, Response, status
from pydantic import BaseModel, Field
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.core.deps import get_db
from app.schemas.common import Envelope, Meta
from app.services.whatsapp_bot import whatsapp_bot_service

router = APIRouter(prefix="/whatsapp", tags=["WhatsApp Bot"])


class WhatsAppSimulateRequest(BaseModel):
    sender_phone: str = Field(default="+919876543210", description="Passenger phone number with country code")
    message: str = Field(
        default="Cleanliness issue at Bandra station platform 1",
        description="Text message body",
    )
    latitude: float | None = Field(default=None, description="Optional GPS latitude")
    longitude: float | None = Field(default=None, description="Optional GPS longitude")


@router.get("/webhook")
async def verify_whatsapp_webhook(
    hub_mode: Annotated[str | None, Query(alias="hub.mode")] = None,
    hub_verify_token: Annotated[str | None, Query(alias="hub.verify_token")] = None,
    hub_challenge: Annotated[str | None, Query(alias="hub.challenge")] = None,
):
    """Meta WhatsApp Business API Webhook Verification Endpoint."""
    if hub_mode == "subscribe" and hub_verify_token == settings.whatsapp_verify_token:
        return Response(content=hub_challenge or "OK", media_type="text/plain")
    raise HTTPException(status_code=403, detail="Invalid verification token")


@router.post("/webhook")
async def handle_whatsapp_webhook(
    request: Request,
    db: Annotated[AsyncSession, Depends(get_db)],
):
    """Handle inbound WhatsApp webhook events from Meta or Twilio."""
    content_type = request.headers.get("content-type", "")

    sender_phone = "+919876543210"
    message_text = ""
    location = None

    if "application/json" in content_type:
        payload = await request.json()
        try:
            entry = payload.get("entry", [])[0]
            changes = entry.get("changes", [])[0]
            value = changes.get("value", {})
            messages = value.get("messages", [])
            if messages:
                msg = messages[0]
                sender_phone = f"+{msg.get('from', '919876543210')}"
                if msg.get("type") == "text":
                    message_text = msg.get("text", {}).get("body", "")
                elif msg.get("type") == "location":
                    loc = msg.get("location", {})
                    location = {"latitude": loc.get("latitude"), "longitude": loc.get("longitude")}
                    message_text = loc.get("name") or "Location report"
        except Exception:
            message_text = payload.get("message") or "WhatsApp report"
    else:
        form = await request.form()
        sender_phone = str(form.get("From") or "+919876543210")
        message_text = str(form.get("Body") or "")

    result = await whatsapp_bot_service.process_inbound_message(
        sender_phone=sender_phone,
        text=message_text,
        location=location,
        db=db,
    )
    return Response(content=result["reply"], media_type="text/plain")


@router.post("/simulate", response_model=Envelope[dict[str, Any]])
async def simulate_whatsapp_message(
    body: WhatsAppSimulateRequest,
    db: Annotated[AsyncSession, Depends(get_db)],
) -> Envelope[dict[str, Any]]:
    """Simulate inbound WhatsApp report for local testing and demonstration."""
    location = None
    if body.latitude is not None and body.longitude is not None:
        location = {"latitude": body.latitude, "longitude": body.longitude}

    result = await whatsapp_bot_service.process_inbound_message(
        sender_phone=body.sender_phone,
        text=body.message,
        location=location,
        db=db,
    )
    return Envelope(data=result, meta=Meta())

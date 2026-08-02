from __future__ import annotations

import uuid
from datetime import datetime, timedelta, timezone
from typing import Annotated, Any

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, Field
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.core.deps import get_db, require_official
from app.models.emergency import EmergencyAlert
from app.models.location import Station
from app.models.user import User
from app.schemas.common import Envelope, Meta
from app.services.scope import enforce_issue_location_scope

router = APIRouter(prefix="/emergency", tags=["Emergency Alerts"])


class EmergencyAlertCreateRequest(BaseModel):
    station_id: uuid.UUID | None = Field(default=None, description="Target station ID (null for line-wide alert)")
    severity: str = Field(default="warning", description="Severity: critical | warning | info")
    title: str = Field(..., min_length=5, max_length=200, description="Short emergency title")
    message: str = Field(..., min_length=10, description="Detailed emergency warning message")
    duration_hours: int = Field(default=4, ge=1, le=72, description="Alert duration in hours")


class EmergencyAlertOut(BaseModel):
    id: uuid.UUID
    station_id: uuid.UUID | None
    station_name: str | None
    station_code: str | None
    severity: str
    title: str
    message: str
    is_active: bool
    expires_at: datetime | None
    created_at: datetime


def alert_to_out(alert: EmergencyAlert) -> EmergencyAlertOut:
    return EmergencyAlertOut(
        id=alert.id,
        station_id=alert.station_id,
        station_name=alert.station.name if alert.station else "System-Wide Corridor",
        station_code=alert.station.code if alert.station else "ALL",
        severity=alert.severity,
        title=alert.title,
        message=alert.message,
        is_active=alert.is_active,
        expires_at=alert.expires_at,
        created_at=alert.created_at,
    )


@router.get("/alerts/active", response_model=Envelope[list[EmergencyAlertOut]])
async def list_active_emergency_alerts(
    db: Annotated[AsyncSession, Depends(get_db)],
    station_id: uuid.UUID | None = None,
) -> Envelope[list[EmergencyAlertOut]]:
    """Public endpoint returning active, non-expired emergency safety alerts."""
    now = datetime.now(timezone.utc)
    query = (
        select(EmergencyAlert)
        .options(selectinload(EmergencyAlert.station))
        .where(
            EmergencyAlert.is_active.is_(True),
            (EmergencyAlert.expires_at.is_(None)) | (EmergencyAlert.expires_at > now),
        )
        .order_by(EmergencyAlert.created_at.desc())
    )

    if station_id:
        query = query.where((EmergencyAlert.station_id == station_id) | (EmergencyAlert.station_id.is_(None)))

    result = await db.execute(query)
    alerts = result.scalars().all()
    return Envelope(data=[alert_to_out(a) for a in alerts], meta=Meta())


@router.post(
    "/alerts",
    status_code=status.HTTP_201_CREATED,
    response_model=Envelope[EmergencyAlertOut],
)
async def create_emergency_alert(
    body: EmergencyAlertCreateRequest,
    db: Annotated[AsyncSession, Depends(get_db)],
    official: Annotated[User, Depends(require_official)],
) -> Envelope[EmergencyAlertOut]:
    """Issue a new emergency safety alert (requires official RBAC)."""
    if body.station_id:
        station = await db.get(Station, body.station_id)
        if not station:
            raise HTTPException(status_code=404, detail="Station not found")
        await enforce_issue_location_scope(official, station)

    expires = datetime.now(timezone.utc) + timedelta(hours=body.duration_hours)
    alert = EmergencyAlert(
        station_id=body.station_id,
        issuer_id=official.id,
        severity=body.severity.lower().strip(),
        title=body.title.strip(),
        message=body.message.strip(),
        is_active=True,
        expires_at=expires,
    )
    db.add(alert)
    await db.flush()
    await db.refresh(alert)

    # Reload with station relation
    res = await db.execute(
        select(EmergencyAlert).options(selectinload(EmergencyAlert.station)).where(EmergencyAlert.id == alert.id)
    )
    return Envelope(data=alert_to_out(res.scalar_one()), meta=Meta())


@router.patch("/alerts/{alert_id}/deactivate", response_model=Envelope[EmergencyAlertOut])
async def deactivate_emergency_alert(
    alert_id: uuid.UUID,
    db: Annotated[AsyncSession, Depends(get_db)],
    official: Annotated[User, Depends(require_official)],
) -> Envelope[EmergencyAlertOut]:
    """Deactivate an active emergency alert."""
    alert = await db.get(EmergencyAlert, alert_id)
    if not alert:
        raise HTTPException(status_code=404, detail="Emergency alert not found")

    if alert.station_id:
        station = await db.get(Station, alert.station_id)
        if station:
            await enforce_issue_location_scope(official, station)

    alert.is_active = False
    await db.flush()

    res = await db.execute(
        select(EmergencyAlert).options(selectinload(EmergencyAlert.station)).where(EmergencyAlert.id == alert.id)
    )
    return Envelope(data=alert_to_out(res.scalar_one()), meta=Meta())

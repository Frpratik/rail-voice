from __future__ import annotations

from typing import Any

from fastapi import APIRouter, HTTPException, status
from pydantic import BaseModel, Field

from app.schemas.common import Envelope, Meta
from app.services.telemetry import telemetry_service

router = APIRouter(prefix="/telemetry", tags=["PNR & Train Telemetry"])


class PNRLookupRequest(BaseModel):
    pnr_number: str = Field(..., min_length=10, max_length=10, description="10-digit Indian Railways PNR number")


class PNRLookupResponse(BaseModel):
    pnr_number: str
    train_number: str
    train_name: str
    coach_number: str
    berth_number: str
    passenger_class: str
    boarding_station: str
    destination_station: str
    upcoming_station_code: str
    upcoming_station_name: str
    eta_minutes: int
    current_latitude: float
    current_longitude: float
    speed_kmh: float
    obhs_assigned: bool
    obhs_vendor_name: str
    obhs_supervisor_mobile: str


@router.post("/pnr-lookup", response_model=Envelope[PNRLookupResponse])
async def lookup_pnr(body: PNRLookupRequest) -> Envelope[PNRLookupResponse]:
    """Lookup 10-digit Indian Railways PNR details and live train telemetry."""
    try:
        data = telemetry_service.lookup_pnr(body.pnr_number)
        return Envelope(data=PNRLookupResponse(**data), meta=Meta())
    except ValueError as err:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(err))


@router.get("/train-status/{train_number}", response_model=Envelope[dict[str, Any]])
async def get_live_train_status(train_number: str) -> Envelope[dict[str, Any]]:
    """Fetch live GPS running status for a moving train."""
    try:
        data = telemetry_service.get_live_train_status(train_number)
        return Envelope(data=data, meta=Meta())
    except ValueError as err:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(err))

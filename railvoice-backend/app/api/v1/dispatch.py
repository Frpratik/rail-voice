from typing import Annotated
from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.session import get_db
from app.schemas.common import Envelope, Meta
from app.schemas.dispatch_schemas import (
    AutoDispatchResultOut,
    DispatchRecommendationOut,
    RosterSummaryOut,
)
from app.services.dispatch_optimizer import dispatch_optimizer_service

router = APIRouter(prefix="/admin/dispatch", tags=["AI Dispatch Optimizer"])

@router.get("/roster", response_model=Envelope[RosterSummaryOut])
async def get_dispatch_roster(
    db: Annotated[AsyncSession, Depends(get_db)],
):
    roster = await dispatch_optimizer_service.get_roster_summary(db)
    return Envelope(data=roster, meta=Meta())

@router.get("/recommendations", response_model=Envelope[list[DispatchRecommendationOut]])
async def get_dispatch_recommendations(
    db: Annotated[AsyncSession, Depends(get_db)],
):
    recommendations = await dispatch_optimizer_service.generate_recommendations(db)
    return Envelope(data=recommendations, meta=Meta())

@router.post("/auto-assign", response_model=Envelope[AutoDispatchResultOut])
async def auto_assign_dispatch(
    db: Annotated[AsyncSession, Depends(get_db)],
):
    result = await dispatch_optimizer_service.auto_dispatch_all(db)
    return Envelope(data=result, meta=Meta())

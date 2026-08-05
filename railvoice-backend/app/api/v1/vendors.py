from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from app.db.session import get_db
from app.services.vendor_penalty import VendorPenaltyService
from app.schemas.vendor_schemas import VendorScorecardResponse

router = APIRouter()

@router.get("/scorecard", response_model=VendorScorecardResponse)
async def get_vendor_scorecard(db: AsyncSession = Depends(get_db)):
    service = VendorPenaltyService(db)
    return await service.get_scorecard()

@router.post("/trigger-engine")
async def trigger_penalty_engine(db: AsyncSession = Depends(get_db)):
    service = VendorPenaltyService(db)
    return await service.trigger_penalty_engine()

@router.post("/penalty-notes/{id}/approve")
async def approve_penalty_note(id: str, db: AsyncSession = Depends(get_db)):
    service = VendorPenaltyService(db)
    return await service.approve_penalty(id)

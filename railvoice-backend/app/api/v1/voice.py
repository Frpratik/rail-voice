from __future__ import annotations

import uuid
from typing import Annotated, Any

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, Field
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.ai.voice_assistant import voice_assistant
from app.core.deps import get_current_user_optional, get_db
from app.models.location import IssueCategory, Station
from app.models.user import User
from app.schemas.common import Envelope, Meta
from app.services.issue_service import issue_service

router = APIRouter(prefix="/voice", tags=["Voice Assistant"])


class VoiceParseRequest(BaseModel):
    transcript: str = Field(..., min_length=3, description="Spoken voice transcript in any vernacular language")


class VoiceCreateIssueRequest(BaseModel):
    transcript: str = Field(..., min_length=5, description="Spoken voice transcript")


class VoiceParseResponse(BaseModel):
    detected_language: str
    station_code: str | None
    station_name: str | None
    category_code: str
    original_transcript: str
    translated_summary: str


@router.post("/parse", response_model=Envelope[VoiceParseResponse])
async def parse_voice_transcript(body: VoiceParseRequest) -> Envelope[VoiceParseResponse]:
    """Parse spoken vernacular transcript and extract station, category, and English summary."""
    result = voice_assistant.process_voice_input(body.transcript)
    return Envelope(data=VoiceParseResponse(**result), meta=Meta())


@router.post("/create-issue", status_code=status.HTTP_201_CREATED, response_model=Envelope[dict[str, Any]])
async def create_issue_from_voice(
    body: VoiceCreateIssueRequest,
    db: Annotated[AsyncSession, Depends(get_db)],
    current_user: Annotated[User | None, Depends(get_current_user_optional)],
) -> Envelope[dict[str, Any]]:
    """Create structured grievance record directly from spoken vernacular input."""
    parsed = voice_assistant.process_voice_input(body.transcript)

    # 1. Resolve Station
    station = None
    if parsed["station_code"]:
        station = await db.scalar(select(Station).where(Station.code == parsed["station_code"]))

    if not station:
        station = await db.scalar(select(Station).where(Station.code == "BA"))  # Default Bandra
    if not station:
        raise HTTPException(status_code=404, detail="Station not found")

    # 2. Resolve Category
    category = await db.scalar(select(IssueCategory).where(IssueCategory.code == parsed["category_code"]))

    # 3. Resolve User
    creator = current_user
    if not creator:
        creator = User(
            id=uuid.uuid4(),
            display_name="Voice Reporter",
            is_anonymous=True,
            anonymous_session_id=str(uuid.uuid4()),
        )
        db.add(creator)
        await db.flush()

    # 4. Create Issue
    issue = await issue_service.create_issue(
        db=db,
        creator=creator,
        station_id=station.id,
        title=parsed["translated_summary"][:100],
        description=f"{parsed['translated_summary']}\n\nOriginal Spoken Transcript ({parsed['detected_language'].upper()}): {parsed['original_transcript']}",
        force_create=True,
        divergence_reason="Voice report submitted via spoken vernacular assistant",
    )

    return Envelope(
        data={
            "issue_id": str(issue.id),
            "issue_number": issue.issue_number,
            "station_code": station.code,
            "station_name": station.name,
            "detected_language": parsed["detected_language"],
            "translated_summary": parsed["translated_summary"],
        },
        meta=Meta(),
    )

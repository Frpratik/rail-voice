from __future__ import annotations

from typing import Annotated
import uuid

from fastapi import APIRouter, Depends, Query
from sqlalchemy import or_, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.core.deps import get_db
from app.models.issue import Issue
from app.schemas.common import Envelope, Meta
from app.schemas.mappers import issue_to_out

router = APIRouter(prefix="/search", tags=["Search"])


@router.get("")
async def text_search(
    db: Annotated[AsyncSession, Depends(get_db)],
    q: str = Query(..., min_length=2),
    station_id: uuid.UUID | None = None,
    limit: int = Query(20, ge=1, le=50),
) -> Envelope[dict]:
    pattern = f"%{q.strip()}%"
    conditions = [
        Issue.is_public.is_(True),
        or_(
            Issue.title.ilike(pattern),
            Issue.description.ilike(pattern),
            Issue.issue_number.ilike(pattern),
        ),
    ]
    if station_id:
        conditions.append(Issue.station_id == station_id)

    query = (
        select(Issue)
        .options(
            selectinload(Issue.station),
            selectinload(Issue.category),
            selectinload(Issue.creator),
            selectinload(Issue.photos),
        )
        .where(*conditions)
        .order_by(Issue.created_at.desc())
        .limit(limit)
    )
    issues = (await db.execute(query)).scalars().all()

    payload = [
        {
            "issue": issue_to_out(i).model_dump(mode="json"),
            "relevance_score": 1.0,
            "match_type": "text",
        }
        for i in issues
    ]
    return Envelope(data={"results": payload}, meta=Meta())


@router.post("/semantic")
async def semantic_search(
    db: Annotated[AsyncSession, Depends(get_db)],
    body: dict,
) -> Envelope[dict]:
    q = body.get("query", "")
    station_id = body.get("station_id")
    limit = min(int(body.get("limit", 20)), 50)
    sid = uuid.UUID(station_id) if station_id else None
    return await text_search(db=db, q=q, station_id=sid, limit=limit)

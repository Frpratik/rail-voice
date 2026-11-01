from __future__ import annotations

from typing import Annotated
import uuid

from fastapi import APIRouter, Depends, Query
from sqlalchemy import or_, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.core.deps import get_db
from app.models.issue import Issue
from app.models.location import Station
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
    terms = [t for t in q.split() if t][:8]
    conditions = [Issue.is_public.is_(True)]
    for term in terms:
        escaped = term.replace("\\", "\\\\").replace("%", "\\%").replace("_", "\\_")
        pattern = f"%{escaped}%"
        conditions.append(
            or_(
                Issue.title.ilike(pattern, escape="\\"),
                Issue.description.ilike(pattern, escape="\\"),
                Issue.issue_number.ilike(pattern, escape="\\"),
                Issue.station.has(Station.name.ilike(pattern, escape="\\")),
            )
        )
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


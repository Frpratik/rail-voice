from __future__ import annotations

from datetime import datetime, timedelta, timezone
from typing import Annotated
import uuid

from fastapi import APIRouter, Depends, Query
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.ai.search import hybrid_search_service
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
    results = await hybrid_search_service.search(
        db, q, station_id=station_id, limit=limit
    )
    if not results:
        return Envelope(data={"results": []}, meta=Meta())

    issue_ids = [uuid.UUID(r.issue_id) for r in results]
    issues_result = await db.execute(
        select(Issue)
        .options(selectinload(Issue.station), selectinload(Issue.category))
        .where(Issue.id.in_(issue_ids))
    )
    issue_map = {i.id: i for i in issues_result.scalars().all()}

    payload = []
    for r in results:
        issue = issue_map.get(uuid.UUID(r.issue_id))
        if issue:
            payload.append(
                {
                    "issue": issue_to_out(issue).model_dump(mode="json"),
                    "relevance_score": r.relevance_score,
                    "match_type": r.match_type,
                }
            )

    return Envelope(data={"results": payload}, meta=Meta())


@router.post("/semantic")
async def semantic_search(
    db: Annotated[AsyncSession, Depends(get_db)],
    body: dict,
) -> Envelope[dict]:
    query = body.get("query", "")
    station_id = body.get("station_id")
    limit = min(int(body.get("limit", 20)), 50)
    sid = uuid.UUID(station_id) if station_id else None
    results = await hybrid_search_service.search(db, query, station_id=sid, limit=limit)
    return Envelope(
        data={"results": [r.__dict__ for r in results]},
        meta=Meta(),
    )

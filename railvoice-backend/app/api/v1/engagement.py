"""Passenger engagement routes plus the public transparency endpoints."""

import uuid
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Query, status
from pydantic import BaseModel, Field
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.core.deps import get_current_user, get_db, get_reporter_user
from app.core.enums import TERMINAL_STATUSES
from app.models.issue import Issue, IssueFollower, StationFavourite
from app.models.location import Station
from app.models.user import User
from app.schemas.common import Envelope, Meta
from app.schemas.mappers import issue_to_out, station_to_out
from app.services import engagement, insights

router = APIRouter(tags=["Engagement"])


class RatingRequest(BaseModel):
    rating: int = Field(..., ge=1, le=5)
    comment: str | None = Field(None, max_length=500)


async def _station_by_code(db: AsyncSession, code: str) -> Station:
    station = (
        await db.execute(select(Station).where(Station.code == code.upper()))
    ).scalar_one_or_none()
    if not station:
        raise HTTPException(status_code=404, detail="Station not found")
    return station


async def _public_issue(db: AsyncSession, issue_id: uuid.UUID) -> Issue:
    issue = await db.get(Issue, issue_id)
    if not issue or not issue.is_public:
        raise HTTPException(status_code=404, detail="Issue not found")
    return issue


@router.get("/stations/nearest")
async def nearest_station(
    db: Annotated[AsyncSession, Depends(get_db)],
    lat: float = Query(..., ge=-90, le=90),
    lng: float = Query(..., ge=-180, le=180),
) -> Envelope[dict]:
    ranked = await engagement.nearest_stations(db, lat, lng)
    return Envelope(
        data={
            "items": [
                {**station_to_out(s).model_dump(mode="json"), "distance_km": round(km, 2)}
                for s, km in ranked
            ]
        },
        meta=Meta(),
    )


@router.get("/stations/{station_code}/stats")
async def station_stats(
    station_code: str,
    db: Annotated[AsyncSession, Depends(get_db)],
) -> Envelope[dict]:
    station = await _station_by_code(db, station_code)
    data = await insights.transparency(db)
    entry = next((s for s in data["stations"] if s["code"] == station.code), None)
    return Envelope(
        data=entry
        or {
            "code": station.code,
            "name": station.name,
            "reports": 0,
            "open": 0,
            "fixed": 0,
            "fix_rate": None,
            "avg_fix_hours": None,
            "avg_rating": None,
        },
        meta=Meta(),
    )


@router.post("/issues/{issue_id}/follow")
async def follow(
    issue_id: uuid.UUID,
    db: Annotated[AsyncSession, Depends(get_db)],
    user: Annotated[User, Depends(get_reporter_user)],
) -> Envelope[dict]:
    await _public_issue(db, issue_id)
    await engagement.follow_issue(db, issue_id, user.id)
    return Envelope(data={"following": True}, meta=Meta())


@router.delete("/issues/{issue_id}/follow")
async def unfollow(
    issue_id: uuid.UUID,
    db: Annotated[AsyncSession, Depends(get_db)],
    user: Annotated[User, Depends(get_reporter_user)],
) -> Envelope[dict]:
    await engagement.unfollow_issue(db, issue_id, user.id)
    return Envelope(data={"following": False}, meta=Meta())


@router.post("/issues/{issue_id}/rating")
async def rate(
    issue_id: uuid.UUID,
    body: RatingRequest,
    db: Annotated[AsyncSession, Depends(get_db)],
    user: Annotated[User, Depends(get_reporter_user)],
) -> Envelope[dict]:
    issue = await _public_issue(db, issue_id)
    try:
        await engagement.rate_issue(db, issue, user, body.rating, body.comment)
    except PermissionError as exc:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=str(exc)) from exc
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)) from exc
    return Envelope(data=await engagement.rating_summary(db, issue_id), meta=Meta())


@router.post("/stations/{station_code}/favourite")
async def favourite_station(
    station_code: str,
    db: Annotated[AsyncSession, Depends(get_db)],
    user: Annotated[User, Depends(get_reporter_user)],
) -> Envelope[dict]:
    station = await _station_by_code(db, station_code)
    await engagement.set_favourite(db, station.id, user.id, True)
    return Envelope(data={"favourite": True}, meta=Meta())


@router.delete("/stations/{station_code}/favourite")
async def unfavourite_station(
    station_code: str,
    db: Annotated[AsyncSession, Depends(get_db)],
    user: Annotated[User, Depends(get_reporter_user)],
) -> Envelope[dict]:
    station = await _station_by_code(db, station_code)
    await engagement.set_favourite(db, station.id, user.id, False)
    return Envelope(data={"favourite": False}, meta=Meta())


@router.get("/me/favourites")
async def my_favourites(
    db: Annotated[AsyncSession, Depends(get_db)],
    user: Annotated[User, Depends(get_current_user)],
) -> Envelope[dict]:
    result = await db.execute(
        select(Station.code)
        .join(StationFavourite, StationFavourite.station_id == Station.id)
        .where(StationFavourite.user_id == user.id)
    )
    return Envelope(data={"codes": list(result.scalars().all())}, meta=Meta())


@router.get("/me/following")
async def my_following(
    db: Annotated[AsyncSession, Depends(get_db)],
    user: Annotated[User, Depends(get_reporter_user)],
    limit: int = Query(50, ge=1, le=100),
) -> Envelope[dict]:
    result = await db.execute(
        select(Issue)
        .options(
            selectinload(Issue.station),
            selectinload(Issue.category),
            selectinload(Issue.photos),
        )
        .join(IssueFollower, IssueFollower.issue_id == Issue.id)
        .where(IssueFollower.user_id == user.id, Issue.is_public.is_(True))
        .order_by(Issue.updated_at.desc())
        .limit(limit)
    )
    return Envelope(
        data={"items": [issue_to_out(i).model_dump(mode="json") for i in result.scalars().all()]},
        meta=Meta(),
    )


@router.get("/me/reputation")
async def my_reputation(
    db: Annotated[AsyncSession, Depends(get_db)],
    user: Annotated[User, Depends(get_reporter_user)],
) -> Envelope[dict]:
    return Envelope(data=await engagement.reputation(db, user), meta=Meta())


@router.get("/me/export")
async def export_my_data(
    db: Annotated[AsyncSession, Depends(get_db)],
    user: Annotated[User, Depends(get_reporter_user)],
) -> Envelope[dict]:
    return Envelope(data=await engagement.export_user_data(db, user), meta=Meta())


@router.post("/me/delete")
async def delete_my_account(
    db: Annotated[AsyncSession, Depends(get_db)],
    user: Annotated[User, Depends(get_reporter_user)],
) -> Envelope[dict]:
    await engagement.delete_account(db, user)
    return Envelope(data={"deleted": True}, meta=Meta())


@router.get("/public/transparency")
async def public_transparency(
    db: Annotated[AsyncSession, Depends(get_db)],
    days: int = Query(90, ge=7, le=365),
) -> Envelope[dict]:
    return Envelope(data=await insights.transparency(db, days), meta=Meta())


@router.get("/public/leaderboard")
async def public_leaderboard(
    db: Annotated[AsyncSession, Depends(get_db)],
) -> Envelope[dict]:
    board = await insights.passenger_leaderboard(db)
    stations = (await insights.transparency(db))["stations"]
    return Envelope(
        data={
            "passengers": board,
            "stations": [s for s in stations if s["reports"] >= 1][:10],
        },
        meta=Meta(),
    )


@router.get("/public/open-count")
async def public_open_count(
    db: Annotated[AsyncSession, Depends(get_db)],
) -> Envelope[dict]:
    count = await db.scalar(
        select(func.count())
        .select_from(Issue)
        .where(
            Issue.is_public.is_(True),
            Issue.status.notin_([s.value for s in TERMINAL_STATUSES]),
        )
    )
    return Envelope(data={"open": count or 0}, meta=Meta())

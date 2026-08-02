from __future__ import annotations

from typing import Annotated

from fastapi import APIRouter, Depends
from pydantic import BaseModel
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.core.deps import get_current_user, get_db
from app.models.gamification import UserReputation
from app.models.issue import Issue
from app.models.location import Station
from app.models.user import User
from app.schemas.common import Envelope, Meta
from app.services.gamification_service import gamification_service

router = APIRouter(prefix="/gamification", tags=["Gamification & Leaderboards"])


class UserLeaderboardEntry(BaseModel):
    rank: int
    user_id: str
    display_name: str
    avatar_url: str | None
    points: int
    tier: str
    badge_slugs: list[str]
    reports_count: int


class StationLeaderboardEntry(BaseModel):
    rank: int
    station_id: str
    station_code: str
    station_name: str
    total_issues: int
    resolved_issues: int
    resolution_rate_pct: float


class UserReputationProfile(BaseModel):
    points: int
    tier: str
    badge_slugs: list[str]
    reports_count: int
    verifications_count: int


@router.get("/leaderboard/users", response_model=Envelope[list[UserLeaderboardEntry]])
async def get_user_leaderboard(
    db: Annotated[AsyncSession, Depends(get_db)],
) -> Envelope[list[UserLeaderboardEntry]]:
    """Return top 20 civic champions ranked by karma points."""
    result = await db.execute(
        select(UserReputation)
        .options(selectinload(UserReputation.user))
        .order_by(UserReputation.points.desc())
        .limit(20)
    )
    reps = result.scalars().all()

    entries = []
    for idx, rep in enumerate(reps, start=1):
        user_name = rep.user.display_name if rep.user else "Civic Contributor"
        avatar = rep.user.avatar_url if rep.user else None
        entries.append(
            UserLeaderboardEntry(
                rank=idx,
                user_id=str(rep.user_id),
                display_name=user_name,
                avatar_url=avatar,
                points=rep.points,
                tier=rep.tier,
                badge_slugs=rep.badge_slugs or [],
                reports_count=rep.reports_count,
            )
        )
    return Envelope(data=entries, meta=Meta())


@router.get("/leaderboard/stations", response_model=Envelope[list[StationLeaderboardEntry]])
async def get_station_leaderboard(
    db: Annotated[AsyncSession, Depends(get_db)],
) -> Envelope[list[StationLeaderboardEntry]]:
    """Return station rankings based on resolution speed and cleanliness stats."""
    stations_res = await db.execute(select(Station).where(Station.is_active.is_(True)).order_by(Station.sequence_order))
    stations = stations_res.scalars().all()

    entries = []
    for idx, st in enumerate(stations, start=1):
        total = await db.scalar(select(func.count(Issue.id)).where(Issue.station_id == st.id)) or 0
        resolved = (
            await db.scalar(
                select(func.count(Issue.id)).where(Issue.station_id == st.id, Issue.status == "resolved")
            )
            or 0
        )
        rate = round((resolved / total * 100), 1) if total > 0 else 100.0

        entries.append(
            StationLeaderboardEntry(
                rank=idx,
                station_id=str(st.id),
                station_code=st.code,
                station_name=st.name,
                total_issues=total,
                resolved_issues=resolved,
                resolution_rate_pct=rate,
            )
        )

    # Sort stations by resolution_rate_pct desc
    entries.sort(key=lambda x: x.resolution_rate_pct, reverse=True)
    for idx, entry in enumerate(entries, start=1):
        entry.rank = idx

    return Envelope(data=entries[:20], meta=Meta())


@router.get("/profile/me", response_model=Envelope[UserReputationProfile])
async def get_my_reputation(
    db: Annotated[AsyncSession, Depends(get_db)],
    current_user: Annotated[User, Depends(get_current_user)],
) -> Envelope[UserReputationProfile]:
    """Return authenticated user's karma points, tier, and badges."""
    rep = await gamification_service.get_or_create_reputation(db, current_user.id)
    return Envelope(
        data=UserReputationProfile(
            points=rep.points,
            tier=rep.tier,
            badge_slugs=rep.badge_slugs or [],
            reports_count=rep.reports_count,
            verifications_count=rep.verifications_count,
        ),
        meta=Meta(),
    )

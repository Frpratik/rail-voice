"""Passenger engagement: nearest station, follows, favourites, ratings, reputation, privacy."""

from __future__ import annotations

import math
import re
import uuid
from datetime import datetime, timezone

from sqlalchemy import func, select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.enums import IssueStatus, Visibility
from app.models.issue import (
    Comment,
    Issue,
    IssueFollower,
    IssueRating,
    IssueSupport,
    IssueTimelineEvent,
    StationFavourite,
)
from app.models.location import Station
from app.models.user import Notification, RefreshToken, User

# Words that are rejected outright. Staff moderation handles anything subtler.
_BLOCKED_WORDS = {
    "fuck", "fucking", "bitch", "asshole", "bastard", "cunt",
    "madarchod", "bhenchod", "behenchod", "chutiya", "chutiye", "gandu", "bhosdike",
}
_WORD_RE = re.compile(r"[a-z]+")

RATEABLE = {
    IssueStatus.COMPLETED.value,
    IssueStatus.VERIFIED_COMPLETE.value,
    IssueStatus.CLOSED.value,
}


def contains_abuse(*texts: str | None) -> bool:
    for text in texts:
        if text and _BLOCKED_WORDS & set(_WORD_RE.findall(text.lower())):
            return True
    return False


def distance_km(lat1: float, lng1: float, lat2: float, lng2: float) -> float:
    phi1, phi2 = math.radians(lat1), math.radians(lat2)
    dphi = math.radians(lat2 - lat1)
    dlam = math.radians(lng2 - lng1)
    a = math.sin(dphi / 2) ** 2 + math.cos(phi1) * math.cos(phi2) * math.sin(dlam / 2) ** 2
    return 6371 * 2 * math.asin(math.sqrt(a))


async def nearest_stations(
    db: AsyncSession, lat: float, lng: float, limit: int = 3
) -> list[tuple[Station, float]]:
    stations = (await db.execute(select(Station).where(Station.is_active.is_(True)))).scalars().all()
    ranked = sorted(
        ((s, distance_km(lat, lng, float(s.latitude), float(s.longitude))) for s in stations),
        key=lambda pair: pair[1],
    )
    return ranked[:limit]


async def follow_issue(db: AsyncSession, issue_id: uuid.UUID, user_id: uuid.UUID) -> None:
    existing = await db.scalar(
        select(func.count())
        .select_from(IssueFollower)
        .where(IssueFollower.issue_id == issue_id, IssueFollower.user_id == user_id)
    )
    if existing:
        return
    try:
        async with db.begin_nested():
            db.add(IssueFollower(issue_id=issue_id, user_id=user_id))
            await db.flush()
    except IntegrityError:
        return  # A concurrent request already followed it.


async def unfollow_issue(db: AsyncSession, issue_id: uuid.UUID, user_id: uuid.UUID) -> None:
    row = (
        await db.execute(
            select(IssueFollower).where(
                IssueFollower.issue_id == issue_id, IssueFollower.user_id == user_id
            )
        )
    ).scalar_one_or_none()
    if row:
        await db.delete(row)


async def notify_followers(
    db: AsyncSession,
    issue: Issue,
    *,
    kind: str,
    title: str,
    body: str,
    skip_user_ids: set[uuid.UUID | None] | None = None,
) -> int:
    rows = await db.execute(select(IssueFollower.user_id).where(IssueFollower.issue_id == issue.id))
    recipients = set(rows.scalars().all()) - (skip_user_ids or set())
    for user_id in recipients:
        db.add(Notification(user_id=user_id, type=kind, title=title[:200], body=body, issue_id=issue.id))
    return len(recipients)


async def set_favourite(db: AsyncSession, station_id: uuid.UUID, user_id: uuid.UUID, on: bool) -> None:
    row = (
        await db.execute(
            select(StationFavourite).where(
                StationFavourite.station_id == station_id, StationFavourite.user_id == user_id
            )
        )
    ).scalar_one_or_none()
    if on and not row:
        db.add(StationFavourite(station_id=station_id, user_id=user_id))
    elif not on and row:
        await db.delete(row)
    await db.flush()


async def rate_issue(
    db: AsyncSession, issue: Issue, user: User, rating: int, comment: str | None
) -> None:
    if issue.status not in RATEABLE:
        raise ValueError("You can rate a report once it has been fixed")
    involved = issue.creator_id == user.id or bool(
        await db.scalar(
            select(func.count())
            .select_from(IssueSupport)
            .where(IssueSupport.issue_id == issue.id, IssueSupport.user_id == user.id)
        )
    )
    if not involved:
        raise PermissionError("Only people who reported or backed this can rate the fix")

    row = (
        await db.execute(
            select(IssueRating).where(IssueRating.issue_id == issue.id, IssueRating.user_id == user.id)
        )
    ).scalar_one_or_none()
    note = (comment or "").strip() or None
    if contains_abuse(note):
        raise ValueError("Please remove offensive language")
    if row:
        row.rating = rating
        row.comment = note
    else:
        db.add(IssueRating(issue_id=issue.id, user_id=user.id, rating=rating, comment=note))
    await db.flush()


async def rating_summary(db: AsyncSession, issue_id: uuid.UUID) -> dict:
    avg, count = (
        await db.execute(
            select(func.avg(IssueRating.rating), func.count(IssueRating.id)).where(
                IssueRating.issue_id == issue_id
            )
        )
    ).one()
    return {"average": round(float(avg), 1) if avg is not None else None, "count": count or 0}


BADGES = [
    ("first_report", "First report", "Filed your first report", lambda s: s["reports"] >= 1),
    ("regular", "Regular reporter", "Filed 5 reports", lambda s: s["reports"] >= 5),
    ("backer", "Community backer", "Backed 10 reports from others", lambda s: s["backed"] >= 10),
    ("fixer", "Problem solver", "3 of your reports got fixed", lambda s: s["fixed"] >= 3),
    ("voice", "Station voice", "Earned 100 points", lambda s: s["points"] >= 100),
]


def points_for(reports: int, backed: int, comments: int, fixed: int) -> int:
    return reports * 10 + backed * 2 + comments + fixed * 5


async def reputation(db: AsyncSession, user: User) -> dict:
    reports = await db.scalar(
        select(func.count())
        .select_from(Issue)
        .where(Issue.creator_id == user.id, Issue.status != IssueStatus.SPAM.value)
    )
    fixed = await db.scalar(
        select(func.count())
        .select_from(Issue)
        .where(Issue.creator_id == user.id, Issue.status == IssueStatus.CLOSED.value)
    )
    backed = await db.scalar(
        select(func.count())
        .select_from(IssueSupport)
        .join(Issue, Issue.id == IssueSupport.issue_id)
        .where(IssueSupport.user_id == user.id, Issue.creator_id != user.id)
    )
    comments = await db.scalar(
        select(func.count())
        .select_from(Comment)
        .where(Comment.user_id == user.id, Comment.is_hidden.is_(False))
    )
    stats = {
        "reports": reports or 0,
        "backed": backed or 0,
        "comments": comments or 0,
        "fixed": fixed or 0,
    }
    stats["points"] = points_for(stats["reports"], stats["backed"], stats["comments"], stats["fixed"])
    earned = [
        {"code": code, "name": name, "description": desc}
        for code, name, desc, test in BADGES
        if test(stats)
    ]
    return {**stats, "badges": earned}


async def export_user_data(db: AsyncSession, user: User) -> dict:
    issues = (await db.execute(select(Issue).where(Issue.creator_id == user.id))).scalars().all()
    comments = (await db.execute(select(Comment).where(Comment.user_id == user.id))).scalars().all()
    return {
        "exported_at": datetime.now(timezone.utc).isoformat(),
        "profile": {
            "display_name": user.display_name,
            "email": user.email,
            "mobile_last4": user.mobile_last4,
            "joined_at": user.created_at.isoformat() if user.created_at else None,
        },
        "reports": [
            {
                "issue_number": i.issue_number,
                "title": i.title,
                "description": i.description,
                "status": i.status,
                "created_at": i.created_at.isoformat() if i.created_at else None,
            }
            for i in issues
        ],
        "comments": [
            {"body": c.body, "created_at": c.created_at.isoformat() if c.created_at else None}
            for c in comments
        ],
    }


async def delete_account(db: AsyncSession, user: User) -> None:
    """Soft delete and strip identifiers. Reports stay as a public record, without the name."""
    now = datetime.now(timezone.utc)
    user.display_name = "Deleted user"
    user.mobile_hash = None
    user.mobile_last4 = None
    user.email = None
    user.google_id = None
    user.avatar_url = None
    user.is_active = False
    user.deleted_at = now
    tokens = await db.execute(
        select(RefreshToken).where(RefreshToken.user_id == user.id, RefreshToken.revoked_at.is_(None))
    )
    for token in tokens.scalars().all():
        token.revoked_at = now
    follows = await db.execute(select(IssueFollower).where(IssueFollower.user_id == user.id))
    for row in follows.scalars().all():
        await db.delete(row)
    await db.flush()


def timeline_event(
    issue: Issue,
    *,
    event_type: str,
    actor_id: uuid.UUID | None,
    remarks: str,
    from_status: str | None = None,
    to_status: str | None = None,
    visibility: str = Visibility.PUBLIC.value,
    metadata: dict | None = None,
) -> IssueTimelineEvent:
    return IssueTimelineEvent(
        issue_id=issue.id,
        event_type=event_type,
        from_status=from_status,
        to_status=to_status,
        actor_id=actor_id,
        remarks=remarks,
        visibility=visibility,
        metadata_=metadata or {},
    )

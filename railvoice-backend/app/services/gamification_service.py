from __future__ import annotations

import logging
import uuid

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.gamification import UserReputation

logger = logging.getLogger(__name__)

POINTS_MATRIX = {
    "issue_created": 15,
    "resolution_confirmed": 25,
    "upvote_given": 2,
}


def calculate_tier(points: int) -> str:
    if points >= 500:
        return "platinum"
    if points >= 200:
        return "gold"
    if points >= 50:
        return "silver"
    return "bronze"


class GamificationService:
    async def get_or_create_reputation(
        self, db: AsyncSession, user_id: uuid.UUID
    ) -> UserReputation:
        rep = await db.scalar(
            select(UserReputation).where(UserReputation.user_id == user_id)
        )
        if not rep:
            rep = UserReputation(
                user_id=user_id,
                points=0,
                tier="bronze",
                badge_slugs=["first_step"],
                reports_count=0,
                verifications_count=0,
            )
            db.add(rep)
            await db.flush()
        return rep

    async def award_points(
        self, db: AsyncSession, user_id: uuid.UUID, action_type: str
    ) -> UserReputation:
        rep = await self.get_or_create_reputation(db, user_id)
        delta = POINTS_MATRIX.get(action_type, 5)
        rep.points += delta

        if action_type == "issue_created":
            rep.reports_count += 1
        elif action_type == "resolution_confirmed":
            rep.verifications_count += 1

        rep.tier = calculate_tier(rep.points)

        badges = set(rep.badge_slugs or [])
        if rep.reports_count >= 1:
            badges.add("first_reporter")
        if rep.reports_count >= 10:
            badges.add("station_sentinel")
        if rep.points >= 200:
            badges.add("corridor_guardian")
        rep.badge_slugs = list(badges)

        await db.flush()
        return rep


gamification_service = GamificationService()

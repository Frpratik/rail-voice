from __future__ import annotations

import logging
import uuid
from datetime import datetime, timedelta, timezone

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.core.config import settings
from app.core.enums import IssueStatus, TimelineEventType, Visibility
from app.core.security import (
    create_access_token,
    create_refresh_token,
    hash_value,
)
from app.models.issue import Comment, Issue, IssueSupport, IssueTimelineEvent
from app.models.location import Station
from app.models.user import OtpRequest, RefreshToken, Role, User, UserRole

logger = logging.getLogger(__name__)

ISSUE_RESPONSE_LOAD = (
    selectinload(Issue.station),
    selectinload(Issue.category),
    selectinload(Issue.creator),
    selectinload(Issue.photos),
)


class AuthService:
    async def request_otp(self, db: AsyncSession, mobile: str) -> None:
        import secrets
        from app.services.sms import get_sms_provider

        mobile_hash = hash_value(mobile)
        if settings.otp_mock_mode:
            otp = settings.otp_mock_code
        else:
            length = max(4, min(8, settings.otp_length))
            otp = "".join(str(secrets.randbelow(10)) for _ in range(length))

        expires = datetime.now(timezone.utc) + timedelta(seconds=settings.otp_ttl_seconds)
        row = OtpRequest(
            mobile_hash=mobile_hash,
            otp_hash=hash_value(otp),
            expires_at=expires,
        )
        db.add(row)
        await db.flush()

        try:
            await get_sms_provider().send_otp(mobile, otp)
        except Exception:
            await db.delete(row)
            await db.flush()
            raise

    async def verify_otp(self, db: AsyncSession, mobile: str, otp: str) -> User:
        mobile_hash = hash_value(mobile)
        result = await db.execute(
            select(OtpRequest)
            .where(OtpRequest.mobile_hash == mobile_hash, OtpRequest.verified_at.is_(None))
            .order_by(OtpRequest.created_at.desc())
            .limit(1)
        )
        otp_row = result.scalar_one_or_none()
        if not otp_row or otp_row.expires_at < datetime.now(timezone.utc):
            raise ValueError("OTP expired or not found")
        if otp_row.attempts >= 3:
            raise ValueError("Too many OTP attempts")
        if otp_row.otp_hash != hash_value(otp):
            otp_row.attempts += 1
            await db.flush()
            raise ValueError("Invalid OTP")

        otp_row.verified_at = datetime.now(timezone.utc)
        user = await self._get_or_create_user_by_mobile(db, mobile, mobile_hash)
        user.is_verified = True
        user.last_login_at = datetime.now(timezone.utc)
        await self._ensure_passenger_role(db, user)
        return user

    async def create_anonymous_user(self, db: AsyncSession) -> User:
        user = User(
            display_name="Anonymous",
            is_anonymous=True,
            anonymous_session_id=uuid.uuid4(),
            is_active=True,
        )
        db.add(user)
        await db.flush()
        return user

    async def _get_or_create_user_by_mobile(
        self, db: AsyncSession, mobile: str, mobile_hash: str
    ) -> User:
        result = await db.execute(select(User).where(User.mobile_hash == mobile_hash))
        user = result.scalar_one_or_none()
        if user:
            return user
        last4 = mobile[-4:] if len(mobile) >= 4 else "0000"
        user = User(
            mobile_hash=mobile_hash,
            mobile_last4=last4,
            display_name=f"Commuter {last4}",
            is_verified=True,
            is_active=True,
        )
        db.add(user)
        await db.flush()
        return user

    async def _ensure_passenger_role(self, db: AsyncSession, user: User) -> None:
        from app.core.enums import RoleCode

        role_res = await db.execute(select(Role).where(Role.code == RoleCode.PASSENGER.value))
        role = role_res.scalar_one_or_none()
        if not role:
            return
        has_role = await db.scalar(
            select(func.count()).select_from(UserRole).where(
                UserRole.user_id == user.id,
                UserRole.role_id == role.id,
                UserRole.revoked_at.is_(None),
            )
        )
        if not has_role:
            db.add(UserRole(user_id=user.id, role_id=role.id))
            await db.flush()

    async def issue_tokens(
        self, db: AsyncSession, user: User, *, family_id: uuid.UUID | None = None
    ) -> tuple[str, str, datetime]:
        access_token = create_access_token(str(user.id))
        raw_refresh, token_hash, expires_at = create_refresh_token(user.id)
        family = family_id or uuid.uuid4()
        row = RefreshToken(
            user_id=user.id,
            token_hash=token_hash,
            family_id=family,
            expires_at=expires_at,
        )
        db.add(row)
        await db.flush()
        return access_token, raw_refresh, expires_at

    async def refresh_tokens(
        self, db: AsyncSession, raw_refresh: str
    ) -> tuple[User, str, str]:
        token_hash = hash_value(raw_refresh)
        result = await db.execute(select(RefreshToken).where(RefreshToken.token_hash == token_hash))
        row = result.scalar_one_or_none()
        now = datetime.now(timezone.utc)
        if not row:
            raise ValueError("Invalid refresh token")

        if row.revoked_at is not None:
            # Revoke entire family if reuse detected
            from app.db.session import async_session_factory
            async with async_session_factory() as side:
                async with side.begin():
                    family_tokens = await side.execute(
                        select(RefreshToken).where(
                            RefreshToken.family_id == row.family_id,
                            RefreshToken.revoked_at.is_(None),
                        )
                    )
                    for t in family_tokens.scalars().all():
                        t.revoked_at = now
            raise ValueError("Refresh token reuse detected")

        if row.expires_at < now:
            row.revoked_at = now
            raise ValueError("Refresh token expired")

        row.revoked_at = now
        user = await db.get(User, row.user_id)
        if not user or not user.is_active:
            raise ValueError("User inactive")

        access_token, new_refresh, _ = await self.issue_tokens(db, user, family_id=row.family_id)
        return user, access_token, new_refresh


class IssueService:
    async def generate_issue_number(self, db: AsyncSession, zone_code: str) -> str:
        year = datetime.now(timezone.utc).year
        prefix = f"RV-{zone_code}-{year}-"
        result = await db.execute(
            select(func.count()).select_from(Issue).where(Issue.issue_number.like(f"{prefix}%"))
        )
        count = (result.scalar() or 0) + 1
        return f"{prefix}{count:06d}"

    async def create_issue(
        self,
        db: AsyncSession,
        *,
        creator: User,
        station_id: uuid.UUID,
        description: str,
        title: str | None = None,
        category_id: uuid.UUID | None = None,
        platform_id: uuid.UUID | None = None,
        train_number: str | None = None,
        coach_number: str | None = None,
        pnr_number: str | None = None,
        berth_number: str | None = None,
        upcoming_station_code: str | None = None,
        is_emergency: bool = False,
        latitude: float | None = None,
        longitude: float | None = None,
    ) -> Issue:
        if creator.is_anonymous:
            day_ago = datetime.now(timezone.utc) - timedelta(hours=24)
            created_today = await db.scalar(
                select(func.count())
                .select_from(Issue)
                .where(Issue.creator_id == creator.id, Issue.created_at >= day_ago)
            )
            if (created_today or 0) >= settings.anonymous_daily_issue_limit:
                raise ValueError("Anonymous daily issue limit reached")

        station_result = await db.execute(
            select(Station).options(selectinload(Station.zone)).where(Station.id == station_id)
        )
        station = station_result.scalar_one_or_none()
        if not station:
            raise ValueError("Station not found")

        zone_code = station.zone.code if station.zone else "WR"
        issue_number = await self.generate_issue_number(db, zone_code)
        now = datetime.now(timezone.utc)

        issue = Issue(
            issue_number=issue_number,
            zone_id=station.zone_id,
            division_id=station.division_id,
            station_id=station_id,
            platform_id=platform_id,
            category_id=category_id,
            creator_id=creator.id,
            title=title or (description[:60] + "..." if len(description) > 60 else description),
            description=description.strip(),
            status=IssueStatus.SUBMITTED.value,
            is_emergency=is_emergency,
            is_public=True,
            train_number=train_number,
            coach_number=coach_number,
            pnr_number=pnr_number,
            berth_number=berth_number,
            upcoming_station_code=upcoming_station_code,
            latitude=latitude,
            longitude=longitude,
            support_count=1,  # Creator automatically upvotes their issue
            comment_count=0,
            created_at=now,
            updated_at=now,
        )
        db.add(issue)
        await db.flush()

        # Add initial creator support
        db.add(IssueSupport(issue_id=issue.id, user_id=creator.id))

        # Add timeline event
        db.add(
            IssueTimelineEvent(
                issue_id=issue.id,
                event_type=TimelineEventType.SUBMITTED.value,
                to_status=issue.status,
                actor_id=creator.id,
                remarks="Issue submitted by citizen",
                visibility=Visibility.PUBLIC.value,
            )
        )
        await db.flush()

        result = await db.execute(
            select(Issue).options(*ISSUE_RESPONSE_LOAD).where(Issue.id == issue.id)
        )
        return result.scalar_one()

    async def support_issue(self, db: AsyncSession, user: User, issue_id: uuid.UUID) -> IssueSupport:
        issue = await db.get(Issue, issue_id)
        if not issue:
            raise ValueError("Issue not found")

        existing = await db.execute(
            select(IssueSupport).where(IssueSupport.issue_id == issue_id, IssueSupport.user_id == user.id)
        )
        if existing.scalar_one_or_none():
            raise ValueError("Already supported")

        support = IssueSupport(issue_id=issue_id, user_id=user.id)
        db.add(support)
        issue.support_count += 1
        await db.flush()
        return support

    async def get_issue_detail(self, db: AsyncSession, issue_id: uuid.UUID) -> Issue | None:
        result = await db.execute(
            select(Issue)
            .options(
                *ISSUE_RESPONSE_LOAD,
                selectinload(Issue.photos),
                selectinload(Issue.timeline_events),
                selectinload(Issue.comments).selectinload(Comment.user),
            )
            .where(Issue.id == issue_id)
        )
        return result.scalar_one_or_none()


auth_service = AuthService()
issue_service = IssueService()

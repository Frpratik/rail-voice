from __future__ import annotations

import uuid
from datetime import datetime, timedelta, timezone

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.ai.duplicate import duplicate_detection_service
from app.ai.pipeline import issue_ai_pipeline
from app.core.config import settings
from app.core.enums import IssueStatus, TimelineEventType, Visibility
from app.core.security import hash_value
from app.models.issue import Comment, Issue, IssueSupport, IssueTimelineEvent
from app.ai.priority import compute_priority_score
from app.models.location import Station
from app.models.user import OtpRequest, RefreshToken, Role, User, UserRole


ISSUE_RESPONSE_LOAD = (
    selectinload(Issue.station),
    selectinload(Issue.category),
    selectinload(Issue.creator),
    selectinload(Issue.photos),
)


class AuthService:
    async def request_otp(self, db: AsyncSession, mobile: str) -> None:
        mobile_hash = hash_value(mobile)
        otp = settings.otp_mock_code if settings.otp_mock_mode else "000000"
        expires = datetime.now(timezone.utc) + timedelta(minutes=5)
        db.add(
            OtpRequest(
                mobile_hash=mobile_hash,
                otp_hash=hash_value(otp),
                expires_at=expires,
            )
        )

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
        user = User(
            display_name=f"User {mobile[-4:]}",
            mobile_hash=mobile_hash,
            is_verified=True,
            is_active=True,
        )
        db.add(user)
        await db.flush()
        return user

    async def _ensure_passenger_role(self, db: AsyncSession, user: User) -> None:
        role_result = await db.execute(select(Role).where(Role.code == "passenger"))
        role = role_result.scalar_one()
        existing = await db.execute(
            select(UserRole).where(
                UserRole.user_id == user.id,
                UserRole.role_id == role.id,
                UserRole.revoked_at.is_(None),
            )
        )
        if not existing.scalar_one_or_none():
            db.add(UserRole(user_id=user.id, role_id=role.id))

    async def upsert_google_user(
        self,
        db: AsyncSession,
        *,
        google_id: str,
        email: str | None,
        name: str,
        avatar_url: str | None = None,
    ) -> User:
        result = await db.execute(select(User).where(User.google_id == google_id))
        user = result.scalar_one_or_none()
        if not user and email:
            result = await db.execute(select(User).where(User.email == email))
            user = result.scalar_one_or_none()
            if user:
                user.google_id = google_id

        if not user:
            user = User(
                google_id=google_id,
                email=email,
                display_name=name or (email.split("@")[0] if email else "Google User"),
                avatar_url=avatar_url,
                is_verified=True,
                is_active=True,
                is_anonymous=False,
            )
            db.add(user)
            await db.flush()
        else:
            user.display_name = name or user.display_name
            if avatar_url:
                user.avatar_url = avatar_url
            if email and not user.email:
                user.email = email
            user.is_verified = True
            user.is_anonymous = False

        user.last_login_at = datetime.now(timezone.utc)
        await self._ensure_passenger_role(db, user)
        return user

    async def issue_tokens(self, db: AsyncSession, user: User, *, family_id: uuid.UUID | None = None):
        """Create access JWT + rotated refresh token. Returns (access, refresh_value, family_id)."""
        from app.core.security import create_access_token, create_refresh_token_value

        access_token = create_access_token(str(user.id))
        refresh_value = create_refresh_token_value()
        family = family_id or uuid.uuid4()
        db.add(
            RefreshToken(
                user_id=user.id,
                token_hash=hash_value(refresh_value),
                family_id=family,
                expires_at=datetime.now(timezone.utc)
                + timedelta(days=settings.refresh_token_expire_days),
            )
        )
        return access_token, refresh_value, family

    async def rotate_refresh_token(self, db: AsyncSession, refresh_value: str) -> tuple[User, str, str]:
        """Validate refresh token, rotate within family, detect reuse."""
        token_hash = hash_value(refresh_value)
        result = await db.execute(select(RefreshToken).where(RefreshToken.token_hash == token_hash))
        row = result.scalar_one_or_none()
        now = datetime.now(timezone.utc)

        if not row:
            raise ValueError("Invalid refresh token")

        if row.revoked_at is not None:
            # Reuse of revoked token → revoke entire family
            family_tokens = await db.execute(
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
    def __init__(self) -> None:
        from app.ai.duplicate import duplicate_detection_service

        self.duplicate_service = duplicate_detection_service

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
        platform_id: uuid.UUID | None = None,
        train_number: str | None = None,
        coach_number: str | None = None,
        latitude: float | None = None,
        longitude: float | None = None,
        force_create: bool = False,
        divergence_reason: str | None = None,
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

        if not force_create:
            similar = await self.duplicate_service.find_similar(
                db, description=description, station_id=station_id, title=title
            )
            if similar:
                raise DuplicateFoundError(similar)

        if force_create and (not divergence_reason or len(divergence_reason.strip()) < 10):
            raise ValueError("divergence_reason required when force_create is true")

        station_result = await db.execute(
            select(Station).options(selectinload(Station.zone)).where(Station.id == station_id)
        )
        station = station_result.scalar_one_or_none()
        if not station:
            raise ValueError("Station not found")

        zone_code = station.zone.code if station.zone else "WR"
        issue_number = await self.generate_issue_number(db, zone_code)
        now = datetime.now(timezone.utc)

        analysis = await issue_ai_pipeline.analyze(
            description=description.strip(),
            title=title,
            is_anonymous=creator.is_anonymous,
            has_photo=False,
        )

        issue = Issue(
            issue_number=issue_number,
            zone_id=station.zone_id,
            division_id=station.division_id,
            station_id=station_id,
            platform_id=platform_id,
            creator_id=creator.id,
            title=title,
            description=description.strip(),
            status=IssueStatus.SUBMITTED.value,
            train_number=train_number,
            coach_number=coach_number,
            latitude=latitude,
            longitude=longitude,
            divergence_reason=divergence_reason,
            edit_window_expires_at=now + timedelta(minutes=settings.issue_edit_window_minutes),
            created_at=now,
            updated_at=now,
        )
        await issue_ai_pipeline.apply_to_issue(db, issue, analysis)
        db.add(issue)
        await db.flush()

        db.add(
            IssueTimelineEvent(
                issue_id=issue.id,
                event_type=TimelineEventType.SUBMITTED.value,
                to_status=issue.status,
                actor_id=creator.id,
                remarks="Issue submitted"
                if issue.is_public
                else "Issue held for spam review",
                visibility=Visibility.PUBLIC.value if issue.is_public else Visibility.INTERNAL.value,
            )
        )
        await db.flush()

        try:
            from app.core.config import settings as _settings
            from app.workers.tasks import recalc_trending_scores

            if _settings.celery_enabled:
                recalc_trending_scores.delay()
        except Exception:
            pass

        result = await db.execute(
            select(Issue).options(*ISSUE_RESPONSE_LOAD).where(Issue.id == issue.id)
        )
        return result.scalar_one()

    async def support_issue(self, db: AsyncSession, user: User, issue_id: uuid.UUID) -> IssueSupport:
        issue = await db.get(Issue, issue_id)
        if not issue:
            raise ValueError("Issue not found")
        if issue.status in {s.value for s in IssueStatus if s in IssueStatus}:
            pass
        existing = await db.execute(
            select(IssueSupport).where(IssueSupport.issue_id == issue_id, IssueSupport.user_id == user.id)
        )
        if existing.scalar_one_or_none():
            raise ValueError("Already supported")

        support = IssueSupport(issue_id=issue_id, user_id=user.id)
        db.add(support)
        issue.support_count += 1
        issue.priority_score = compute_priority_score(
            support_count=issue.support_count,
            severity=issue.severity,
            created_at=issue.created_at or datetime.now(timezone.utc),
            trending_score=float(issue.trending_score or 0),
            ai_priority_score=float(issue.ai_priority_score or 0.5),
        )
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


class DuplicateFoundError(Exception):
    def __init__(self, similar: list) -> None:
        self.similar = similar
        super().__init__("Similar issues found")


auth_service = AuthService()
issue_service = IssueService()

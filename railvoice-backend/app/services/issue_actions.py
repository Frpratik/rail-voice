"""Passenger-side issue actions: similar reports, withdraw, confirm/reopen, flags, staff alerts."""

from __future__ import annotations

import re
import uuid
from datetime import datetime, timezone

from sqlalchemy import and_, func, or_, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.ai import duplicates
from app.ai.client import AIUnavailable, ai_enabled
from app.core.config import settings
from app.core.enums import (
    TERMINAL_STATUSES,
    IssueStatus,
    RoleCode,
    TimelineEventType,
    Visibility,
)
from app.models.issue import Comment, Issue, IssueFlag, IssueTimelineEvent
from app.models.location import IssueCategory, Station
from app.models.user import Notification, Role, User, UserRole

FLAG_REASONS = {"spam", "abuse", "false_report", "duplicate", "other"}

# A reporter may withdraw only before staff have started work.
WITHDRAWABLE = {
    IssueStatus.SUBMITTED.value,
    IssueStatus.UNDER_REVIEW.value,
    IssueStatus.VERIFIED.value,
}
# A reporter may confirm or dispute the fix once staff say it is done.
CONFIRMABLE = {IssueStatus.COMPLETED.value, IssueStatus.VERIFIED_COMPLETE.value}

_STOPWORDS = {
    "the", "and", "for", "with", "this", "that", "from", "near", "are", "was", "not",
    "has", "have", "since", "there", "their", "been", "very", "platform", "station",
}


def _terms(text: str) -> set[str]:
    return {w for w in re.findall(r"[a-z0-9]+", text.lower()) if len(w) > 2 and w not in _STOPWORDS}


async def find_similar_issues(
    db: AsyncSession,
    *,
    station_id: uuid.UUID,
    category_code: str | None,
    text: str | None,
    limit: int = 5,
) -> list[tuple[Issue, str | None]]:
    """Open public reports at the same station, best matches first, with an AI reason when available."""
    open_filter = Issue.status.notin_([s.value for s in TERMINAL_STATUSES])
    result = await db.execute(
        select(Issue)
        .options(
            selectinload(Issue.station),
            selectinload(Issue.category),
            selectinload(Issue.photos),
        )
        .where(Issue.station_id == station_id, Issue.is_public.is_(True), open_filter)
        .order_by(Issue.created_at.desc())
        .limit(100)
    )
    issues = list(result.scalars().all())
    wanted = _terms(text or "")

    scored: list[tuple[float, Issue]] = []
    for issue in issues:
        score = 0.0
        if category_code and issue.category and issue.category.code == category_code:
            score += 2.0
        overlap = wanted & _terms(f"{issue.title or ''} {issue.description}")
        score += len(overlap) * 1.5
        score += min(issue.support_count, 50) / 50
        scored.append((score, issue))
    scored.sort(key=lambda pair: pair[0], reverse=True)

    # AI understands paraphrases and other languages; keyword matching is the fallback.
    if text and len(text.strip()) >= 12 and ai_enabled() and issues:
        try:
            ranked = [issue for _, issue in scored]
            reasons = await duplicates.same_problem(
                text,
                [
                    {
                        "issue_number": i.issue_number,
                        "title": i.title,
                        "description": i.description,
                        "category": i.category.name if i.category else None,
                    }
                    for i in ranked
                ],
            )
            return [(i, reasons[i.issue_number]) for i in ranked if i.issue_number in reasons][:limit]
        except AIUnavailable:
            pass

    keyword = [
        (score, issue)
        for score, issue in scored
        # Without a text match, only same-category reports are worth showing.
        if score - min(issue.support_count, 50) / 50 >= 2.0
        or wanted & _terms(f"{issue.title or ''} {issue.description}")
    ]
    return [(issue, None) for _, issue in keyword[:limit]]


async def staff_for_station(db: AsyncSession, station: Station) -> list[User]:
    """Station-scoped officials for this station; main admins if there are none."""
    scoped = await db.execute(
        select(User)
        .join(UserRole, UserRole.user_id == User.id)
        .join(Role, Role.id == UserRole.role_id)
        .where(
            User.is_active.is_(True),
            User.deleted_at.is_(None),
            UserRole.revoked_at.is_(None),
            Role.code.in_(
                [
                    RoleCode.STATION_MODERATOR.value,
                    RoleCode.STATION_MANAGER.value,
                    RoleCode.DIVISIONAL_OFFICER.value,
                ]
            ),
            or_(
                and_(UserRole.location_type == "station", UserRole.location_id == station.id),
                and_(UserRole.location_type == "division", UserRole.location_id == station.division_id),
                User.assigned_station_id == station.id,
            ),
        )
        .distinct()
    )
    staff = list(scoped.scalars().unique().all())
    if staff:
        return staff

    main = await db.execute(
        select(User)
        .join(UserRole, UserRole.user_id == User.id)
        .join(Role, Role.id == UserRole.role_id)
        .where(
            User.is_active.is_(True),
            User.deleted_at.is_(None),
            UserRole.revoked_at.is_(None),
            UserRole.location_type.is_(None),
            Role.code.in_([RoleCode.SUPER_ADMIN.value, RoleCode.RAILWAY_ADMIN.value]),
        )
        .distinct()
    )
    return list(main.scalars().unique().all())


async def notify_staff(
    db: AsyncSession,
    station: Station,
    *,
    kind: str,
    title: str,
    body: str,
    issue_id: uuid.UUID | None,
    extra_user_ids: set[uuid.UUID] | None = None,
    skip_user_id: uuid.UUID | None = None,
) -> int:
    recipients = {u.id for u in await staff_for_station(db, station)}
    recipients |= extra_user_ids or set()
    recipients.discard(skip_user_id)
    for user_id in recipients:
        db.add(
            Notification(
                user_id=user_id,
                type=kind,
                title=title[:200],
                body=body,
                issue_id=issue_id,
            )
        )
    return len(recipients)


async def enforce_daily_limit(db: AsyncSession, creator: User) -> None:
    since = datetime.now(timezone.utc).replace(hour=0, minute=0, second=0, microsecond=0)
    count = await db.scalar(
        select(func.count()).select_from(Issue).where(Issue.creator_id == creator.id, Issue.created_at >= since)
    )
    if (count or 0) >= settings.daily_issue_limit:
        raise ValueError(
            f"Daily limit of {settings.daily_issue_limit} reports reached. Please try again tomorrow."
        )


def _timeline(
    issue: Issue,
    *,
    event_type: str,
    from_status: str | None,
    to_status: str | None,
    actor: User,
    remarks: str,
) -> IssueTimelineEvent:
    return IssueTimelineEvent(
        issue_id=issue.id,
        event_type=event_type,
        from_status=from_status,
        to_status=to_status,
        actor_id=actor.id,
        actor_role="reporter",
        remarks=remarks,
        visibility=Visibility.PUBLIC.value,
    )


async def withdraw_issue(db: AsyncSession, issue: Issue, user: User, reason: str | None) -> Issue:
    if issue.creator_id != user.id:
        raise PermissionError("Only the reporter can withdraw this report")
    if issue.status not in WITHDRAWABLE:
        raise ValueError("This report is already being worked on and can't be withdrawn")
    previous = issue.status
    issue.status = IssueStatus.WITHDRAWN.value
    issue.is_public = False  # Off the feed, search and staff queue; the reporter can still open it.
    issue.closed_at = datetime.now(timezone.utc)
    db.add(
        _timeline(
            issue,
            event_type=TimelineEventType.CLOSED.value,
            from_status=previous,
            to_status=issue.status,
            actor=user,
            remarks=f"Withdrawn by reporter. {reason or ''}".strip(),
        )
    )
    return issue


async def confirm_resolution(
    db: AsyncSession, issue: Issue, user: User, *, fixed: bool, remarks: str | None
) -> Issue:
    if issue.creator_id != user.id:
        raise PermissionError("Only the reporter can confirm the fix")
    if issue.status not in CONFIRMABLE:
        raise ValueError("This report hasn't been marked as fixed yet")

    previous = issue.status
    now = datetime.now(timezone.utc)
    station = await db.get(Station, issue.station_id)
    notes = (remarks or "").strip()

    if fixed:
        issue.status = IssueStatus.CLOSED.value
        issue.closed_at = now
        db.add(
            _timeline(
                issue,
                event_type=TimelineEventType.CLOSED.value,
                from_status=previous,
                to_status=issue.status,
                actor=user,
                remarks=f"Reporter confirmed the problem is fixed. {notes}".strip(),
            )
        )
    else:
        issue.status = IssueStatus.UNDER_REVIEW.value
        issue.resolved_at = None
        db.add(
            _timeline(
                issue,
                event_type=TimelineEventType.STATUS_CHANGE.value,
                from_status=previous,
                to_status=issue.status,
                actor=user,
                remarks=f"Reporter says the problem is NOT fixed. {notes}".strip(),
            )
        )
        if station:
            await notify_staff(
                db,
                station,
                kind="reopened",
                title=f"Reopened: {issue.issue_number}",
                body=f"Reporter says it isn't fixed. {notes}".strip()[:300],
                issue_id=issue.id,
                extra_user_ids={issue.assignee_id} if issue.assignee_id else None,
                skip_user_id=user.id,
            )
    return issue


async def flag_target(
    db: AsyncSession,
    *,
    user: User,
    issue: Issue,
    comment: Comment | None,
    reason: str,
    note: str | None,
) -> IssueFlag:
    if reason not in FLAG_REASONS:
        raise ValueError("Unknown reason")
    if comment is None and issue.creator_id == user.id:
        raise ValueError("You can't flag your own report")
    if comment is not None and comment.user_id == user.id:
        raise ValueError("You can't flag your own comment")

    existing = await db.scalar(
        select(func.count())
        .select_from(IssueFlag)
        .where(
            IssueFlag.user_id == user.id,
            IssueFlag.issue_id == issue.id,
            IssueFlag.comment_id.is_(None) if comment is None else IssueFlag.comment_id == comment.id,
        )
    )
    if existing:
        raise ValueError("You've already flagged this")

    flag = IssueFlag(
        issue_id=issue.id,
        comment_id=comment.id if comment else None,
        user_id=user.id,
        reason=reason,
        note=(note or "").strip()[:500] or None,
    )
    db.add(flag)
    await db.flush()

    # Tell staff once enough different people have flagged the same thing.
    open_count = await db.scalar(
        select(func.count())
        .select_from(IssueFlag)
        .where(
            IssueFlag.issue_id == issue.id,
            IssueFlag.resolved_at.is_(None),
            IssueFlag.comment_id.is_(None) if comment is None else IssueFlag.comment_id == comment.id,
        )
    )
    if open_count == settings.flag_notify_threshold:
        station = await db.get(Station, issue.station_id)
        if station:
            what = "comment" if comment else "report"
            await notify_staff(
                db,
                station,
                kind="flagged",
                title=f"Flagged {what}: {issue.issue_number}",
                body=f"{open_count} passengers flagged this {what}. Please review.",
                issue_id=issue.id,
            )
    return flag


async def category_by_code(db: AsyncSession, code: str) -> IssueCategory | None:
    return (await db.execute(select(IssueCategory).where(IssueCategory.code == code))).scalar_one_or_none()

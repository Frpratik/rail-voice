from datetime import datetime, timedelta, timezone
from typing import Annotated, Literal
import uuid

from pydantic import BaseModel, Field
from fastapi import APIRouter, Depends, HTTPException, Query, Response, status
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.core.config import settings
from app.core.deps import get_db, require_official
from app.core.enums import IssueStatus, TERMINAL_STATUSES, TimelineEventType, Visibility
from app.models.issue import Comment, Issue, IssueFlag, IssueTimelineEvent
from app.models.user import Notification, User
from app.schemas.common import (
    AssignRequest,
    DashboardKPIs,
    Envelope,
    EscalateRequest,
    Meta,
    NotifyMainAdminRequest,
    StatusUpdateRequest,
)
from app.schemas.mappers import issue_to_out
from app.services import engagement
from app.services.issue_service import ISSUE_RESPONSE_LOAD, issue_service
from app.services.sla import is_overdue
from app.services.report_service import issues_to_pdf, issues_to_xlsx
from app.services.scope import apply_issue_location_scope, enforce_issue_location_scope

router = APIRouter(prefix="/admin", tags=["Admin"])


VALID_TRANSITIONS: dict[str, set[str]] = {
    IssueStatus.SUBMITTED.value: {IssueStatus.VERIFIED.value, IssueStatus.REJECTED.value, IssueStatus.UNDER_REVIEW.value},
    IssueStatus.UNDER_REVIEW.value: {IssueStatus.VERIFIED.value, IssueStatus.REJECTED.value},
    IssueStatus.VERIFIED.value: {
        IssueStatus.ASSIGNED.value,
        IssueStatus.FORWARDED_DIVISION.value,
        IssueStatus.FORWARDED_STATION_MANAGER.value,
        IssueStatus.FORWARDED_ZONE.value,
        IssueStatus.ACTION_STARTED.value,
    },
    IssueStatus.ASSIGNED.value: {
        IssueStatus.ACTION_STARTED.value,
        IssueStatus.FORWARDED_STATION_MANAGER.value,
        IssueStatus.WORK_IN_PROGRESS.value,
        IssueStatus.FORWARDED_DIVISION.value,
    },
    IssueStatus.FORWARDED_STATION_MANAGER.value: {
        IssueStatus.ASSIGNED.value,
        IssueStatus.FORWARDED_DIVISION.value,
        IssueStatus.ACTION_STARTED.value,
    },
    IssueStatus.FORWARDED_DIVISION.value: {
        IssueStatus.ASSIGNED.value,
        IssueStatus.FORWARDED_ZONE.value,
        IssueStatus.ACTION_STARTED.value,
    },
    IssueStatus.FORWARDED_ZONE.value: {IssueStatus.ASSIGNED.value, IssueStatus.ACTION_STARTED.value},
    IssueStatus.ACTION_STARTED.value: {IssueStatus.WORK_IN_PROGRESS.value, IssueStatus.COMPLETED.value},
    IssueStatus.WORK_IN_PROGRESS.value: {
        IssueStatus.WAITING_FOR_MATERIAL.value,
        IssueStatus.COMPLETED.value,
    },
    IssueStatus.WAITING_FOR_MATERIAL.value: {IssueStatus.WORK_IN_PROGRESS.value},
    IssueStatus.COMPLETED.value: {IssueStatus.VERIFIED_COMPLETE.value, IssueStatus.CLOSED.value},
    IssueStatus.VERIFIED_COMPLETE.value: {IssueStatus.CLOSED.value},
}

ESCALATE_STATUS = {
    "station_manager": IssueStatus.FORWARDED_STATION_MANAGER.value,
    "division": IssueStatus.FORWARDED_DIVISION.value,
    "zone": IssueStatus.FORWARDED_ZONE.value,
}


async def apply_status_change(
    db: AsyncSession,
    issue: Issue,
    officer: User,
    new_status: str,
    remarks: str,
    *,
    visibility: str = Visibility.PUBLIC.value,
) -> IssueTimelineEvent:
    """Validate a transition, then record it and tell the people following the report."""
    allowed = VALID_TRANSITIONS.get(issue.status, set())
    if new_status not in allowed and new_status != issue.status:
        raise ValueError(f"Invalid transition from {issue.status} to {new_status}")

    from_status = issue.status
    issue.status = new_status
    if new_status == IssueStatus.CLOSED.value:
        issue.closed_at = datetime.now(timezone.utc)
    if new_status == IssueStatus.COMPLETED.value:
        issue.resolved_at = datetime.now(timezone.utc)

    event = IssueTimelineEvent(
        issue_id=issue.id,
        event_type="status_change",
        from_status=from_status,
        to_status=new_status,
        actor_id=officer.id,
        remarks=remarks,
        visibility=visibility,
    )
    db.add(event)
    label = new_status.replace("_", " ")
    if issue.creator_id:
        db.add(
            Notification(
                user_id=issue.creator_id,
                type="status_change",
                title=f"Issue {issue.issue_number} updated",
                body=f"Status changed to {label}. {remarks[:120]}",
                issue_id=issue.id,
            )
        )
    await engagement.notify_followers(
        db,
        issue,
        kind="status_change",
        title=f"Update on {issue.issue_number}",
        body=f"Status changed to {label}.",
        skip_user_ids={issue.creator_id, officer.id},
    )
    await db.flush()
    return event


def _scoped_issues(query, officer: User):
    return apply_issue_location_scope(query, officer)


@router.get("/dashboard", response_model=Envelope[dict])
async def admin_dashboard(
    db: Annotated[AsyncSession, Depends(get_db)],
    officer: Annotated[User, Depends(require_official)],
) -> Envelope[dict]:
    open_statuses = [s.value for s in IssueStatus if s not in TERMINAL_STATUSES]
    open_count = await db.scalar(
        _scoped_issues(
            select(func.count()).select_from(Issue).where(Issue.status.in_(open_statuses)),
            officer,
        )
    )
    in_progress = await db.scalar(
        _scoped_issues(
            select(func.count())
            .select_from(Issue)
            .where(
                Issue.status.in_(
                    [IssueStatus.WORK_IN_PROGRESS.value, IssueStatus.ACTION_STARTED.value]
                )
            ),
            officer,
        )
    )
    today = datetime.now(timezone.utc).date()
    resolved_today = await db.scalar(
        _scoped_issues(
            select(func.count()).select_from(Issue).where(func.date(Issue.closed_at) == today),
            officer,
        )
    )
    emergency = await db.scalar(
        _scoped_issues(
            select(func.count())
            .select_from(Issue)
            .where(
                Issue.is_emergency.is_(True),
                Issue.status.notin_([s.value for s in TERMINAL_STATUSES]),
            ),
            officer,
        )
    )
    avg_seconds = await db.scalar(
        _scoped_issues(
            select(func.avg(func.extract("epoch", Issue.resolved_at - Issue.created_at)))
            .select_from(Issue)
            .where(Issue.resolved_at.is_not(None)),
            officer,
        )
    )
    open_rows = await db.execute(
        _scoped_issues(
            select(Issue.status, Issue.severity, Issue.created_at, Issue.is_emergency).where(
                Issue.status.in_(open_statuses)
            ),
            officer,
        )
    )
    now = datetime.now(timezone.utc)
    sla_breaches = sum(
        1
        for row in open_rows.all()
        if is_overdue(row.status, row.created_at, row.is_emergency, row.severity, now)
    )
    kpis = DashboardKPIs(
        open_issues=open_count or 0,
        in_progress=in_progress or 0,
        resolved_today=resolved_today or 0,
        avg_resolution_hours=round(float(avg_seconds) / 3600, 1) if avg_seconds is not None else None,
        sla_breaches=sla_breaches,
        emergency_open=emergency or 0,
    )
    top = await db.execute(
        _scoped_issues(
            select(Issue)
            .options(*ISSUE_RESPONSE_LOAD)
            .where(Issue.is_public.is_(True), Issue.status.in_(open_statuses))
            .order_by(Issue.support_count.desc(), Issue.created_at.desc())
            .limit(5),
            officer,
        )
    )
    return Envelope(
        data={
            "kpis": kpis.model_dump(),
            "top_issues": [issue_to_out(i).model_dump(mode="json") for i in top.scalars().all()],
        },
        meta=Meta(),
    )


@router.get("/issues")
async def admin_issue_queue(
    db: Annotated[AsyncSession, Depends(get_db)],
    officer: Annotated[User, Depends(require_official)],
    status_filter: str | None = None,
    department: str | None = None,
    assigned_to_me: bool = False,
    overdue_only: bool = False,
    limit: int = 50,
) -> Envelope[dict]:
    query = (
        select(Issue)
        .options(*ISSUE_RESPONSE_LOAD)
        .where(Issue.is_public.is_(True))
        .order_by(Issue.priority_score.desc(), Issue.created_at.desc())
        .limit(500 if overdue_only else limit)
    )
    if status_filter:
        query = query.where(Issue.status == status_filter)
    if department:
        query = query.where(Issue.department == department)
    if assigned_to_me:
        query = query.where(Issue.assignee_id == officer.id)
    query = _scoped_issues(query, officer)
    result = await db.execute(query)
    issues = list(result.scalars().all())
    if overdue_only:
        issues = [
            i for i in issues if is_overdue(i.status, i.created_at, i.is_emergency, i.severity)
        ][:limit]
    return Envelope(
        data={"items": [issue_to_out(i).model_dump(mode="json") for i in issues]},
        meta=Meta(),
    )


@router.patch("/issues/{issue_id}/status")
async def update_issue_status(
    issue_id: uuid.UUID,
    body: StatusUpdateRequest,
    db: Annotated[AsyncSession, Depends(get_db)],
    officer: Annotated[User, Depends(require_official)],
) -> Envelope[dict]:
    issue = await db.get(Issue, issue_id)
    if not issue:
        raise HTTPException(status_code=404, detail="Issue not found")
    enforce_issue_location_scope(officer, issue)

    from_status = issue.status
    try:
        event = await apply_status_change(
            db, issue, officer, body.status, body.remarks, visibility=body.visibility
        )
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail=str(exc)) from exc
    await db.flush()

    detailed = await issue_service.get_issue_detail(db, issue.id)
    return Envelope(
        data={
            "issue": issue_to_out(detailed).model_dump(mode="json"),
            "timeline_event": {
                "id": str(event.id),
                "from_status": from_status,
                "to_status": body.status,
                "created_at": event.created_at.isoformat() if event.created_at else None,
            },
        },
        meta=Meta(),
    )


@router.post("/issues/{issue_id}/assign")
async def assign_issue(
    issue_id: uuid.UUID,
    body: AssignRequest,
    db: Annotated[AsyncSession, Depends(get_db)],
    officer: Annotated[User, Depends(require_official)],
) -> Envelope[dict]:
    issue = await db.get(Issue, issue_id)
    if not issue:
        raise HTTPException(status_code=404, detail="Issue not found")
    enforce_issue_location_scope(officer, issue)
    assignee = await db.get(User, body.assignee_id)
    if not assignee or not assignee.is_active:
        raise HTTPException(status_code=404, detail="Assignee not found")

    from_status = issue.status
    issue.assignee_id = assignee.id
    issue.assigned_at = datetime.now(timezone.utc)
    if issue.status in {
        IssueStatus.VERIFIED.value,
        IssueStatus.SUBMITTED.value,
        IssueStatus.UNDER_REVIEW.value,
        IssueStatus.FORWARDED_STATION_MANAGER.value,
        IssueStatus.FORWARDED_DIVISION.value,
        IssueStatus.FORWARDED_ZONE.value,
    }:
        issue.status = IssueStatus.ASSIGNED.value

    db.add(
        IssueTimelineEvent(
            issue_id=issue.id,
            event_type=TimelineEventType.ASSIGNED.value,
            from_status=from_status,
            to_status=issue.status,
            actor_id=officer.id,
            remarks=body.remarks,
            visibility=Visibility.PUBLIC.value,
            metadata_={"assignee_id": str(assignee.id), "assignee_name": assignee.display_name},
        )
    )
    db.add(
        Notification(
            user_id=assignee.id,
            type="assignment",
            title=f"Assigned: {issue.issue_number}",
            body=body.remarks,
            issue_id=issue.id,
        )
    )
    if issue.creator_id:
        db.add(
            Notification(
                user_id=issue.creator_id,
                type="assignment",
                title=f"Issue {issue.issue_number} assigned",
                body=f"Assigned to {assignee.display_name}",
                issue_id=issue.id,
            )
        )
    await db.flush()
    detailed = await issue_service.get_issue_detail(db, issue.id)
    return Envelope(
        data={"issue": issue_to_out(detailed).model_dump(mode="json")},
        meta=Meta(),
    )


@router.post("/issues/{issue_id}/escalate")
async def escalate_issue(
    issue_id: uuid.UUID,
    body: EscalateRequest,
    db: Annotated[AsyncSession, Depends(get_db)],
    officer: Annotated[User, Depends(require_official)],
) -> Envelope[dict]:
    issue = await db.get(Issue, issue_id)
    if not issue:
        raise HTTPException(status_code=404, detail="Issue not found")
    enforce_issue_location_scope(officer, issue)
    if issue.status in {st.value for st in TERMINAL_STATUSES}:
        raise HTTPException(status_code=422, detail=f"Cannot escalate a {issue.status} issue")
    target_status = ESCALATE_STATUS[body.target]
    from_status = issue.status
    issue.status = target_status
    db.add(
        IssueTimelineEvent(
            issue_id=issue.id,
            event_type=TimelineEventType.ESCALATED.value,
            from_status=from_status,
            to_status=target_status,
            actor_id=officer.id,
            remarks=body.remarks,
            visibility=Visibility.PUBLIC.value,
            metadata_={"target": body.target},
        )
    )
    await engagement.notify_followers(
        db,
        issue,
        kind="escalation",
        title=f"Update on {issue.issue_number}",
        body=f"Escalated to {body.target.replace('_', ' ')}.",
        skip_user_ids={issue.creator_id, officer.id},
    )
    if issue.creator_id:
        db.add(
            Notification(
                user_id=issue.creator_id,
                type="escalation",
                title=f"Issue {issue.issue_number} escalated",
                body=f"Escalated to {body.target.replace('_', ' ')}. {body.remarks[:120]}",
                issue_id=issue.id,
            )
        )
    await db.flush()
    detailed = await issue_service.get_issue_detail(db, issue.id)
    return Envelope(
        data={"issue": issue_to_out(detailed).model_dump(mode="json")},
        meta=Meta(),
    )


@router.get("/officers")
async def list_officers(
    db: Annotated[AsyncSession, Depends(get_db)],
    _: Annotated[User, Depends(require_official)],
) -> Envelope[dict]:
    from app.core.enums import OFFICIAL_ROLES
    from app.models.user import Role, UserRole

    official_codes = {r.value for r in OFFICIAL_ROLES}
    query = (
        select(User)
        .options(selectinload(User.roles).selectinload(UserRole.role))
        .join(UserRole, UserRole.user_id == User.id)
        .join(Role, Role.id == UserRole.role_id)
        .where(
            User.is_active.is_(True),
            User.is_anonymous.is_(False),
            User.deleted_at.is_(None),
            UserRole.revoked_at.is_(None),
            Role.code.in_(official_codes),
        )
        .distinct()
        .limit(200)
    )
    result = await db.execute(query)
    officers = []
    for user in result.scalars().unique().all():
        roles = [
            ur.role.code
            for ur in user.roles
            if ur.revoked_at is None and ur.role and ur.role.code in official_codes
        ]
        if roles:
            officers.append(
                {
                    "id": str(user.id),
                    "display_name": user.display_name,
                    "roles": roles,
                }
            )
    return Envelope(data={"items": officers}, meta=Meta())


@router.get("/reports/issues.xlsx")
async def export_issues_xlsx(
    db: Annotated[AsyncSession, Depends(get_db)],
    officer: Annotated[User, Depends(require_official)],
    station_code: str | None = Query(None),
    status_filter: str | None = Query(None),
    limit: int = Query(500, ge=1, le=2000),
) -> Response:
    from app.models.location import Station

    query = select(Issue).options(selectinload(Issue.station)).where(Issue.is_public.is_(True)).limit(limit)
    if status_filter:
        query = query.where(Issue.status == status_filter)
    if station_code:
        query = query.join(Issue.station).where(Station.code == station_code.upper())
    query = _scoped_issues(query, officer)
    result = await db.execute(query.order_by(Issue.created_at.desc()))
    issues = list(result.scalars().all())
    content = issues_to_xlsx(issues)
    return Response(
        content=content,
        media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        headers={"Content-Disposition": "attachment; filename=railvoice-issues.xlsx"},
    )


@router.get("/reports/issues.pdf")
async def export_issues_pdf(
    db: Annotated[AsyncSession, Depends(get_db)],
    officer: Annotated[User, Depends(require_official)],
    station_code: str | None = Query(None),
    status_filter: str | None = Query(None),
    limit: int = Query(200, ge=1, le=500),
    days: int | None = Query(None, ge=1, le=365),
) -> Response:
    from app.models.location import Station

    query = select(Issue).options(selectinload(Issue.station)).where(Issue.is_public.is_(True)).limit(limit)
    if days:
        query = query.where(Issue.created_at >= datetime.now(timezone.utc) - timedelta(days=days))
    if status_filter:
        query = query.where(Issue.status == status_filter)
    if station_code:
        query = query.join(Issue.station).where(Station.code == station_code.upper())
    query = _scoped_issues(query, officer)
    result = await db.execute(query.order_by(Issue.support_count.desc(), Issue.created_at.desc()))
    issues = list(result.scalars().all())
    content = issues_to_pdf(issues)
    return Response(
        content=content,
        media_type="application/pdf",
        headers={"Content-Disposition": "attachment; filename=railvoice-issues.pdf"},
    )


@router.post("/reports/notify-main")
async def notify_main_admin(
    body: NotifyMainAdminRequest,
    db: Annotated[AsyncSession, Depends(get_db)],
    officer: Annotated[User, Depends(require_official)],
) -> Envelope[dict]:
    """Station Admin sends an official briefing report to Western Railway Main Admins."""
    from app.core.enums import RoleCode
    from app.models.user import Role, UserRole
    from app.services.personas import PERSONA_MAIN_ADMIN, PERSONA_STATION_ADMIN, user_persona
    from app.services.scope import official_location_scopes

    persona = user_persona(officer)
    if persona not in {PERSONA_STATION_ADMIN, PERSONA_MAIN_ADMIN}:
        raise HTTPException(status_code=403, detail="Only station or main admins can send reports")

    open_statuses = [s.value for s in IssueStatus if s not in TERMINAL_STATUSES]
    open_count = await db.scalar(
        _scoped_issues(
            select(func.count()).select_from(Issue).where(Issue.status.in_(open_statuses)),
            officer,
        )
    )
    scopes = official_location_scopes(officer)
    scope_note = "all stations" if scopes is None else "scoped station(s)"

    main_role = (
        await db.execute(select(Role).where(Role.code == RoleCode.SUPER_ADMIN.value))
    ).scalar_one_or_none()
    if main_role is None:
        raise HTTPException(status_code=404, detail="No Main Admin users found")
    main_users = await db.execute(
        select(User)
        .options(selectinload(User.roles).selectinload(UserRole.role))
        .join(UserRole, UserRole.user_id == User.id)
        .where(
            UserRole.role_id == main_role.id,
            UserRole.revoked_at.is_(None),
            User.is_active.is_(True),
        )
    )
    notified = 0
    for main_user in main_users.scalars().unique().all():
        if user_persona(main_user) != PERSONA_MAIN_ADMIN:
            continue
        db.add(
            Notification(
                user_id=main_user.id,
                type="station_report",
                title=f"Report from {officer.display_name}",
                body=f"{body.remarks} · {open_count or 0} open issues ({scope_note})",
                issue_id=None,
            )
        )
        notified += 1

    if notified == 0:
        raise HTTPException(status_code=404, detail="No Main Admin users found")

    await db.flush()
    return Envelope(
        data={"notified": notified, "open_issues": open_count or 0, "scope": scope_note},
        meta=Meta(),
    )


async def _lock_repeat_abuser(db: AsyncSession, user_id: uuid.UUID | None) -> bool:
    """Lock an account once enough of its posts have been removed by staff."""
    if not user_id:
        return False
    author = await db.get(User, user_id)
    if not author or author.is_locked:
        return False
    removed_reports = await db.scalar(
        select(func.count())
        .select_from(Issue)
        .where(Issue.creator_id == user_id, Issue.status == IssueStatus.SPAM.value)
    )
    removed_comments = await db.scalar(
        select(func.count())
        .select_from(Comment)
        .where(Comment.user_id == user_id, Comment.is_hidden.is_(True))
    )
    if (removed_reports or 0) + (removed_comments or 0) < settings.abuse_lock_threshold:
        return False
    author.is_locked = True
    author.locked_at = datetime.now(timezone.utc)
    author.locked_reason = "Repeated rule violations"
    await db.flush()
    return True


class FlagResolveRequest(BaseModel):
    action: Literal["dismiss", "hide"]
    remarks: str | None = Field(None, max_length=500)


@router.get("/flags")
async def list_flags(
    db: Annotated[AsyncSession, Depends(get_db)],
    officer: Annotated[User, Depends(require_official)],
    include_resolved: bool = False,
    limit: int = Query(100, ge=1, le=200),
) -> Envelope[dict]:
    """Passenger flags on reports and comments, newest first, within the officer's scope."""
    query = select(IssueFlag).join(Issue, Issue.id == IssueFlag.issue_id)
    if not include_resolved:
        query = query.where(IssueFlag.resolved_at.is_(None))
    query = _scoped_issues(query, officer).order_by(IssueFlag.created_at.desc()).limit(limit)
    flags = (await db.execute(query)).scalars().unique().all()

    items = []
    for flag in flags:
        issue = flag.issue
        items.append(
            {
                "id": str(flag.id),
                "reason": flag.reason,
                "note": flag.note,
                "created_at": flag.created_at.isoformat() if flag.created_at else None,
                "resolved_at": flag.resolved_at.isoformat() if flag.resolved_at else None,
                "resolution": flag.resolution,
                "reporter": flag.reporter.display_name if flag.reporter else None,
                "target": "comment" if flag.comment_id else "issue",
                "comment_body": flag.comment.body if flag.comment else None,
                "issue": {
                    "id": str(issue.id),
                    "issue_number": issue.issue_number,
                    "title": issue.title,
                    "status": issue.status,
                    "station": issue.station.name if issue.station else None,
                },
            }
        )
    return Envelope(data={"items": items}, meta=Meta())


@router.post("/flags/{flag_id}/resolve")
async def resolve_flag(
    flag_id: uuid.UUID,
    body: FlagResolveRequest,
    db: Annotated[AsyncSession, Depends(get_db)],
    officer: Annotated[User, Depends(require_official)],
) -> Envelope[dict]:
    flag = await db.get(IssueFlag, flag_id)
    if not flag:
        raise HTTPException(status_code=404, detail="Flag not found")
    issue = await db.get(Issue, flag.issue_id)
    if not issue:
        raise HTTPException(status_code=404, detail="Issue not found")
    enforce_issue_location_scope(officer, issue)

    now = datetime.now(timezone.utc)
    author_id = None
    if body.action == "hide":
        if flag.comment_id:
            comment = await db.get(Comment, flag.comment_id)
            author_id = comment.user_id if comment else None
            if comment and not comment.is_hidden:
                comment.is_hidden = True
                if issue.comment_count > 0:
                    issue.comment_count -= 1
        else:
            author_id = issue.creator_id
            previous = issue.status
            issue.status = IssueStatus.SPAM.value
            issue.is_public = False
            db.add(
                IssueTimelineEvent(
                    issue_id=issue.id,
                    event_type=TimelineEventType.STATUS_CHANGE.value,
                    from_status=previous,
                    to_status=issue.status,
                    actor_id=officer.id,
                    remarks=body.remarks or "Removed after passenger flags",
                    visibility=Visibility.INTERNAL.value,
                )
            )

    # Resolve every open flag on the same target at once.
    target = select(IssueFlag).where(
        IssueFlag.issue_id == flag.issue_id,
        IssueFlag.resolved_at.is_(None),
        IssueFlag.comment_id.is_(None) if flag.comment_id is None else IssueFlag.comment_id == flag.comment_id,
    )
    resolved = 0
    for row in (await db.execute(target)).scalars().unique().all():
        row.resolved_at = now
        row.resolved_by = officer.id
        row.resolution = body.action
        resolved += 1
    await db.flush()
    locked = await _lock_repeat_abuser(db, author_id)
    return Envelope(
        data={"resolved": resolved, "action": body.action, "author_locked": locked},
        meta=Meta(),
    )

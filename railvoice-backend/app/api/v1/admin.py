from datetime import date, datetime, timezone
from typing import Annotated
import uuid

from fastapi import APIRouter, Depends, HTTPException, Query, Response, status
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.ai.daily_summary import daily_summary_generator
from app.core.deps import get_db, require_official
from app.core.enums import IssueStatus, TERMINAL_STATUSES, TimelineEventType, Visibility
from app.models.issue import Issue, IssueTimelineEvent
from app.models.user import Notification, User
from app.schemas.common import (
    AssignRequest,
    DashboardKPIs,
    Envelope,
    EscalateRequest,
    Meta,
    StatusUpdateRequest,
)
from app.schemas.mappers import issue_to_out
from app.services.issue_service import ISSUE_RESPONSE_LOAD
from app.services.report_service import issues_to_pdf, issues_to_xlsx

router = APIRouter(prefix="/admin", tags=["Admin"])


VALID_TRANSITIONS: dict[str, set[str]] = {
    IssueStatus.SUBMITTED.value: {IssueStatus.VERIFIED.value, IssueStatus.REJECTED.value, IssueStatus.UNDER_REVIEW.value},
    IssueStatus.UNDER_REVIEW.value: {IssueStatus.VERIFIED.value, IssueStatus.REJECTED.value},
    IssueStatus.VERIFIED.value: {
        IssueStatus.ASSIGNED.value,
        IssueStatus.FORWARDED_DIVISION.value,
        IssueStatus.FORWARDED_STATION_MANAGER.value,
        IssueStatus.FORWARDED_ZONE.value,
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
    IssueStatus.ACTION_STARTED.value: {IssueStatus.WORK_IN_PROGRESS.value},
    IssueStatus.WORK_IN_PROGRESS.value: {
        IssueStatus.WAITING_FOR_MATERIAL.value,
        IssueStatus.COMPLETED.value,
    },
    IssueStatus.WAITING_FOR_MATERIAL.value: {IssueStatus.WORK_IN_PROGRESS.value},
    IssueStatus.COMPLETED.value: {IssueStatus.VERIFIED_COMPLETE.value},
    IssueStatus.VERIFIED_COMPLETE.value: {IssueStatus.CLOSED.value},
}

ESCALATE_STATUS = {
    "station_manager": IssueStatus.FORWARDED_STATION_MANAGER.value,
    "division": IssueStatus.FORWARDED_DIVISION.value,
    "zone": IssueStatus.FORWARDED_ZONE.value,
}


@router.get("/dashboard", response_model=Envelope[dict])
async def admin_dashboard(
    db: Annotated[AsyncSession, Depends(get_db)],
    _: Annotated[User, Depends(require_official)],
) -> Envelope[dict]:
    open_statuses = [s.value for s in IssueStatus if s not in TERMINAL_STATUSES]
    open_count = await db.scalar(select(func.count()).select_from(Issue).where(Issue.status.in_(open_statuses)))
    in_progress = await db.scalar(
        select(func.count())
        .select_from(Issue)
        .where(Issue.status.in_([IssueStatus.WORK_IN_PROGRESS.value, IssueStatus.ACTION_STARTED.value]))
    )
    today = datetime.now(timezone.utc).date()
    resolved_today = await db.scalar(
        select(func.count()).select_from(Issue).where(func.date(Issue.closed_at) == today)
    )
    emergency = await db.scalar(
        select(func.count())
        .select_from(Issue)
        .where(Issue.is_emergency.is_(True), Issue.status.notin_([s.value for s in TERMINAL_STATUSES]))
    )
    kpis = DashboardKPIs(
        open_issues=open_count or 0,
        in_progress=in_progress or 0,
        resolved_today=resolved_today or 0,
        avg_resolution_hours=None,
        sla_breaches=0,
        emergency_open=emergency or 0,
    )
    top = await db.execute(
        select(Issue)
        .options(*ISSUE_RESPONSE_LOAD)
        .where(Issue.is_public.is_(True))
        .order_by(Issue.priority_score.desc())
        .limit(5)
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
    _: Annotated[User, Depends(require_official)],
    status_filter: str | None = None,
    limit: int = 50,
) -> Envelope[dict]:
    query = (
        select(Issue)
        .options(*ISSUE_RESPONSE_LOAD)
        .where(Issue.is_public.is_(True))
        .order_by(Issue.priority_score.desc())
        .limit(limit)
    )
    if status_filter:
        query = query.where(Issue.status == status_filter)
    result = await db.execute(query)
    issues = result.scalars().all()
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

    allowed = VALID_TRANSITIONS.get(issue.status, set())
    if body.status not in allowed and body.status != issue.status:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=f"Invalid transition from {issue.status} to {body.status}",
        )

    from_status = issue.status
    issue.status = body.status
    if body.status == IssueStatus.CLOSED.value:
        issue.closed_at = datetime.now(timezone.utc)
    if body.status == IssueStatus.COMPLETED.value:
        issue.resolved_at = datetime.now(timezone.utc)

    event = IssueTimelineEvent(
        issue_id=issue.id,
        event_type="status_change",
        from_status=from_status,
        to_status=body.status,
        actor_id=officer.id,
        remarks=body.remarks,
        visibility=body.visibility,
    )
    db.add(event)
    if issue.creator_id:
        db.add(
            Notification(
                user_id=issue.creator_id,
                type="status_change",
                title=f"Issue {issue.issue_number} updated",
                body=f"Status changed to {body.status.replace('_', ' ')}. {body.remarks[:120]}",
                issue_id=issue.id,
            )
        )
    await db.flush()

    from app.services.issue_service import issue_service

    detailed = await issue_service.get_issue_detail(db, issue.id)
    return Envelope(
        data={
            "issue": issue_to_out(detailed).model_dump(mode="json"),
            "timeline_event": {
                "id": str(event.id),
                "from_status": from_status,
                "to_status": body.status,
                "created_at": event.created_at.isoformat(),
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
    from app.services.issue_service import issue_service

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
    from app.services.issue_service import issue_service

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
    from app.models.user import UserRole

    result = await db.execute(
        select(User)
        .options(selectinload(User.roles).selectinload(UserRole.role))
        .where(User.is_active.is_(True), User.is_anonymous.is_(False))
        .limit(100)
    )
    officers = []
    official_codes = {r.value for r in OFFICIAL_ROLES}
    for user in result.scalars().all():
        roles = [ur.role.code for ur in user.roles if ur.revoked_at is None and ur.role]
        if any(r in official_codes for r in roles):
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
    _: Annotated[User, Depends(require_official)],
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
    _: Annotated[User, Depends(require_official)],
    station_code: str | None = Query(None),
    status_filter: str | None = Query(None),
    limit: int = Query(200, ge=1, le=500),
) -> Response:
    from app.models.location import Station

    query = select(Issue).options(selectinload(Issue.station)).where(Issue.is_public.is_(True)).limit(limit)
    if status_filter:
        query = query.where(Issue.status == status_filter)
    if station_code:
        query = query.join(Issue.station).where(Station.code == station_code.upper())
    result = await db.execute(query.order_by(Issue.priority_score.desc()))
    issues = list(result.scalars().all())
    content = issues_to_pdf(issues)
    return Response(
        content=content,
        media_type="application/pdf",
        headers={"Content-Disposition": "attachment; filename=railvoice-issues.pdf"},
    )


@router.get("/analytics/ai-insights/daily-summary")
async def daily_ai_summary(
    _: Annotated[User, Depends(require_official)],
    target_date: date | None = Query(None),
) -> Envelope[dict]:
    from sqlalchemy import create_engine
    from sqlalchemy.orm import Session

    from app.core.config import settings

    engine = create_engine(settings.database_url_sync)
    with Session(engine) as session:
        summary = daily_summary_generator.generate(session, target_date)
    return Envelope(data=summary, meta=Meta())


@router.get("/spam-queue")
async def spam_review_queue(
    db: Annotated[AsyncSession, Depends(get_db)],
    _: Annotated[User, Depends(require_official)],
    limit: int = 50,
) -> Envelope[dict]:
    result = await db.execute(
        select(Issue)
        .where(Issue.status == IssueStatus.SPAM.value)
        .order_by(Issue.created_at.desc())
        .limit(limit)
    )
    issues = result.scalars().all()
    return Envelope(
        data={"items": [issue_to_out(i).model_dump(mode="json") for i in issues]},
        meta=Meta(),
    )

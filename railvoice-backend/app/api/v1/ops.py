"""Staff tools: notes, bulk updates, merging, departments, SLA sweep, analytics, audit."""

from __future__ import annotations

import asyncio
import logging
import uuid
from datetime import datetime, timedelta, timezone
from typing import Annotated, Literal

from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel, Field
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.v1.admin import _scoped_issues, apply_status_change
from app.core.config import settings
from app.core.deps import get_db, require_main_admin, require_official
from app.core.enums import IssueStatus, TimelineEventType, Visibility
from app.db.session import async_session_factory
from app.models.issue import Issue, IssueFollower, IssueSupport, IssueTimelineEvent
from app.models.location import Station
from app.models.user import AuthAuditEvent, Notification, User, UserManagementAudit
from app.schemas.common import Envelope, Meta
from app.schemas.mappers import issue_detail_to_out, issue_to_out
from app.services import engagement, insights
from app.services.issue_actions import notify_staff
from app.services.issue_service import ISSUE_RESPONSE_LOAD, issue_service
from app.services.scope import enforce_issue_location_scope
from app.services.sla import is_overdue

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/admin", tags=["Admin Ops"])

DEPARTMENTS = ["cleaning", "electrical", "civil", "mechanical", "security", "commercial", "contractor"]
# Statuses an overdue report can be pushed up from automatically.
AUTO_ESCALATE_FROM = {
    IssueStatus.SUBMITTED.value,
    IssueStatus.UNDER_REVIEW.value,
    IssueStatus.VERIFIED.value,
    IssueStatus.ASSIGNED.value,
    IssueStatus.FORWARDED_STATION_MANAGER.value,
}


class NoteRequest(BaseModel):
    body: str = Field(..., min_length=2, max_length=2000)


class BulkStatusRequest(BaseModel):
    issue_ids: list[uuid.UUID] = Field(..., min_length=1, max_length=50)
    status: str
    remarks: str = Field(..., min_length=5, max_length=2000)


class MergeRequest(BaseModel):
    target_id: uuid.UUID
    remarks: str = Field("Merged with an existing report", max_length=500)


class DepartmentRequest(BaseModel):
    department: Literal[
        "cleaning", "electrical", "civil", "mechanical", "security", "commercial", "contractor"
    ] | None = None


async def _load_scoped(db: AsyncSession, issue_id: uuid.UUID, officer: User) -> Issue:
    issue = await db.get(Issue, issue_id)
    if not issue:
        raise HTTPException(status_code=404, detail="Issue not found")
    enforce_issue_location_scope(officer, issue)
    return issue


@router.get("/departments")
async def list_departments(
    _: Annotated[User, Depends(require_official)],
) -> Envelope[dict]:
    return Envelope(data={"items": DEPARTMENTS}, meta=Meta())


@router.get("/issues/{issue_id}/detail")
async def admin_issue_detail(
    issue_id: uuid.UUID,
    db: Annotated[AsyncSession, Depends(get_db)],
    officer: Annotated[User, Depends(require_official)],
) -> Envelope[dict]:
    await _load_scoped(db, issue_id, officer)
    issue = await issue_service.get_issue_detail(db, issue_id)
    return Envelope(
        data=issue_detail_to_out(issue, include_internal=True).model_dump(mode="json"),
        meta=Meta(),
    )


@router.post("/issues/{issue_id}/notes", status_code=201)
async def add_internal_note(
    issue_id: uuid.UUID,
    body: NoteRequest,
    db: Annotated[AsyncSession, Depends(get_db)],
    officer: Annotated[User, Depends(require_official)],
) -> Envelope[dict]:
    issue = await _load_scoped(db, issue_id, officer)
    event = engagement.timeline_event(
        issue,
        event_type="internal_note",
        actor_id=officer.id,
        remarks=f"{officer.display_name}: {body.body.strip()}",
        visibility=Visibility.INTERNAL.value,
    )
    db.add(event)
    await db.flush()
    return Envelope(data={"id": str(event.id)}, meta=Meta())


@router.patch("/issues/{issue_id}/department")
async def set_department(
    issue_id: uuid.UUID,
    body: DepartmentRequest,
    db: Annotated[AsyncSession, Depends(get_db)],
    officer: Annotated[User, Depends(require_official)],
) -> Envelope[dict]:
    issue = await _load_scoped(db, issue_id, officer)
    issue.department = body.department
    await db.flush()
    return Envelope(data={"department": issue.department}, meta=Meta())


@router.post("/issues/bulk-status")
async def bulk_status(
    body: BulkStatusRequest,
    db: Annotated[AsyncSession, Depends(get_db)],
    officer: Annotated[User, Depends(require_official)],
) -> Envelope[dict]:
    updated: list[str] = []
    skipped: list[dict] = []
    for issue_id in body.issue_ids:
        issue = await db.get(Issue, issue_id)
        if not issue:
            skipped.append({"id": str(issue_id), "reason": "Not found"})
            continue
        try:
            enforce_issue_location_scope(officer, issue)
            await apply_status_change(db, issue, officer, body.status, body.remarks)
        except HTTPException as exc:
            skipped.append({"id": str(issue_id), "reason": str(exc.detail)})
            continue
        except ValueError as exc:
            skipped.append({"id": str(issue_id), "reason": str(exc)})
            continue
        updated.append(str(issue_id))
    return Envelope(data={"updated": updated, "skipped": skipped}, meta=Meta())


@router.post("/issues/{issue_id}/merge")
async def merge_issue(
    issue_id: uuid.UUID,
    body: MergeRequest,
    db: Annotated[AsyncSession, Depends(get_db)],
    officer: Annotated[User, Depends(require_official)],
) -> Envelope[dict]:
    """Close a duplicate and move its backers and followers onto the report that stays."""
    if issue_id == body.target_id:
        raise HTTPException(status_code=400, detail="A report can't be merged into itself")
    source = await _load_scoped(db, issue_id, officer)
    target = await _load_scoped(db, body.target_id, officer)
    if source.station_id != target.station_id:
        raise HTTPException(status_code=400, detail="Only reports at the same station can be merged")
    if not target.is_public or target.status == IssueStatus.DUPLICATE_MERGED.value:
        raise HTTPException(status_code=400, detail="The report to merge into is not open")

    existing = await db.execute(select(IssueSupport.user_id).where(IssueSupport.issue_id == target.id))
    backers = set(existing.scalars().all())
    moving = await db.execute(select(IssueSupport.user_id).where(IssueSupport.issue_id == source.id))
    added = 0
    for user_id in moving.scalars().all():
        if user_id not in backers:
            db.add(IssueSupport(issue_id=target.id, user_id=user_id))
            added += 1
            await engagement.follow_issue(db, target.id, user_id)
    target.support_count += added

    followers = await db.execute(select(IssueFollower.user_id).where(IssueFollower.issue_id == source.id))
    for user_id in followers.scalars().all():
        await engagement.follow_issue(db, target.id, user_id)

    previous = source.status
    source.status = IssueStatus.DUPLICATE_MERGED.value
    source.is_public = False
    source.merged_into_id = target.id
    source.closed_at = datetime.now(timezone.utc)
    db.add(
        engagement.timeline_event(
            source,
            event_type=TimelineEventType.MERGED.value,
            actor_id=officer.id,
            remarks=f"Merged into {target.issue_number}. {body.remarks}",
            from_status=previous,
            to_status=source.status,
        )
    )
    db.add(
        engagement.timeline_event(
            target,
            event_type=TimelineEventType.MERGED.value,
            actor_id=officer.id,
            remarks=f"{source.issue_number} was merged into this report.",
        )
    )
    if source.creator_id:
        db.add(
            Notification(
                user_id=source.creator_id,
                type="merged",
                title=f"{source.issue_number} merged",
                body=f"Your report is being handled under {target.issue_number}.",
                issue_id=target.id,
            )
        )
    await db.flush()
    return Envelope(data={"merged_into": str(target.id), "backers_added": added}, meta=Meta())


async def run_sla_sweep(db: AsyncSession) -> int:
    """Push overdue reports up to the division once, and tell everyone concerned."""
    rows = await db.execute(
        select(Issue).where(
            Issue.is_public.is_(True),
            Issue.auto_escalated.is_(False),
            Issue.status.in_(AUTO_ESCALATE_FROM),
        )
    )
    escalated = 0
    for issue in rows.scalars().all():
        if not is_overdue(issue.status, issue.created_at, issue.is_emergency, issue.severity):
            continue
        previous = issue.status
        issue.status = IssueStatus.FORWARDED_DIVISION.value
        issue.auto_escalated = True
        db.add(
            engagement.timeline_event(
                issue,
                event_type=TimelineEventType.ESCALATED.value,
                actor_id=None,
                remarks="Automatically escalated to the division: past its target time.",
                from_status=previous,
                to_status=issue.status,
            )
        )
        station = await db.get(Station, issue.station_id)
        if station:
            await notify_staff(
                db,
                station,
                kind="escalation",
                title=f"Overdue: {issue.issue_number}",
                body="Past its target time and escalated to the division.",
                issue_id=issue.id,
            )
        await engagement.notify_followers(
            db,
            issue,
            kind="escalation",
            title=f"Update on {issue.issue_number}",
            body="Escalated to the division because it passed its target time.",
        )
        escalated += 1
    await db.flush()
    return escalated


async def sla_sweep_loop() -> None:
    """Background loop started by the app. There is no worker on the free tier."""
    while True:
        await asyncio.sleep(settings.sla_sweep_minutes * 60)
        try:
            async with async_session_factory() as session:
                async with session.begin():
                    count = await run_sla_sweep(session)
            if count:
                logger.info("SLA sweep escalated %s reports", count)
        except Exception:  # noqa: BLE001 - the loop must survive a bad run
            logger.exception("SLA sweep failed")


@router.post("/sla/sweep")
async def sla_sweep(
    db: Annotated[AsyncSession, Depends(get_db)],
    _: Annotated[User, Depends(require_main_admin)],
) -> Envelope[dict]:
    return Envelope(data={"escalated": await run_sla_sweep(db)}, meta=Meta())


@router.get("/analytics")
async def analytics(
    db: Annotated[AsyncSession, Depends(get_db)],
    officer: Annotated[User, Depends(require_official)],
    days: int = Query(30, ge=7, le=365),
) -> Envelope[dict]:
    since = datetime.now(timezone.utc) - timedelta(days=days)
    query = _scoped_issues(insights._analytics_query().where(Issue.created_at >= since), officer)
    rows = (await db.execute(query)).all()
    return Envelope(data=insights.summarise(rows, days=days), meta=Meta())


@router.get("/handover")
async def shift_handover(
    db: Annotated[AsyncSession, Depends(get_db)],
    officer: Annotated[User, Depends(require_official)],
    hours: int = Query(12, ge=1, le=72),
) -> Envelope[dict]:
    """What the next shift needs to know."""
    since = datetime.now(timezone.utc) - timedelta(hours=hours)
    new_rows = await db.execute(
        _scoped_issues(
            select(Issue)
            .options(*ISSUE_RESPONSE_LOAD)
            .where(Issue.created_at >= since, Issue.is_public.is_(True))
            .order_by(Issue.created_at.desc())
            .limit(50),
            officer,
        )
    )
    open_rows = await db.execute(
        _scoped_issues(
            select(Issue)
            .options(*ISSUE_RESPONSE_LOAD)
            .where(Issue.is_public.is_(True))
            .order_by(Issue.priority_score.desc())
            .limit(300),
            officer,
        )
    )
    overdue = [
        i
        for i in open_rows.scalars().all()
        if is_overdue(i.status, i.created_at, i.is_emergency, i.severity)
    ]
    changes = await db.execute(
        _scoped_issues(
            select(
                IssueTimelineEvent.event_type,
                IssueTimelineEvent.remarks,
                IssueTimelineEvent.created_at,
            )
            .join(Issue, Issue.id == IssueTimelineEvent.issue_id)
            .where(IssueTimelineEvent.created_at >= since)
            .order_by(IssueTimelineEvent.created_at.desc())
            .limit(30),
            officer,
        )
    )
    return Envelope(
        data={
            "hours": hours,
            "new_reports": [issue_to_out(i).model_dump(mode="json") for i in new_rows.scalars().all()],
            "overdue": [issue_to_out(i).model_dump(mode="json") for i in overdue[:20]],
            "activity": [
                {
                    "type": event_type,
                    "remarks": remarks,
                    "at": at.isoformat() if at else None,
                }
                for event_type, remarks, at in changes.all()
            ],
        },
        meta=Meta(),
    )


@router.get("/audit")
async def audit_log(
    db: Annotated[AsyncSession, Depends(get_db)],
    _: Annotated[User, Depends(require_main_admin)],
    limit: int = Query(100, ge=1, le=300),
) -> Envelope[dict]:
    auth_rows = await db.execute(
        select(AuthAuditEvent).order_by(AuthAuditEvent.created_at.desc()).limit(limit)
    )
    user_rows = await db.execute(
        select(UserManagementAudit).order_by(UserManagementAudit.created_at.desc()).limit(limit)
    )
    events = [
        {
            "at": e.created_at.isoformat() if e.created_at else None,
            "kind": "sign-in",
            "action": e.event_type,
            "actor": None,
            "target": None,
            "success": e.success,
            "ip": e.ip,
        }
        for e in auth_rows.scalars().all()
    ] + [
        {
            "at": e.created_at.isoformat() if e.created_at else None,
            "kind": "user",
            "action": e.action,
            "actor": e.actor_name,
            "target": e.target_user_name,
            "success": True,
            "ip": e.ip,
        }
        for e in user_rows.scalars().all()
    ]
    events.sort(key=lambda e: e["at"] or "", reverse=True)
    return Envelope(data={"items": events[:limit]}, meta=Meta())

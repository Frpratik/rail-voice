from datetime import date, datetime, timedelta, timezone

from sqlalchemy import create_engine, func, select
from sqlalchemy.orm import sessionmaker

from app.ai.daily_summary import daily_summary_generator
from app.ai.priority import compute_priority_score
from app.ai.trending import compute_trending_score
from app.core.config import settings
from app.models.issue import Issue, IssueSupport
from app.workers.celery_app import celery_app

sync_engine = create_engine(settings.database_url_sync)
SyncSession = sessionmaker(bind=sync_engine)


@celery_app.task(name="app.workers.tasks.recalc_priority_scores", queue="low")
def recalc_priority_scores() -> int:
    updated = 0
    with SyncSession() as session:
        issues = session.execute(select(Issue).where(Issue.is_public.is_(True))).scalars().all()
        for issue in issues:
            issue.priority_score = compute_priority_score(
                support_count=issue.support_count,
                severity=issue.severity,
                created_at=issue.created_at or datetime.now(timezone.utc),
                trending_score=float(issue.trending_score or 0),
                ai_priority_score=float(issue.ai_priority_score or 0.5),
            )
            updated += 1
        session.commit()
    return updated


@celery_app.task(name="app.workers.tasks.recalc_trending_scores", queue="low")
def recalc_trending_scores() -> int:
    now = datetime.now(timezone.utc)
    day_ago = now - timedelta(hours=24)
    week_ago = now - timedelta(days=7)
    updated = 0

    with SyncSession() as session:
        issues = session.execute(select(Issue).where(Issue.is_public.is_(True))).scalars().all()
        for issue in issues:
            supports_24h = session.scalar(
                select(func.count())
                .select_from(IssueSupport)
                .where(IssueSupport.issue_id == issue.id, IssueSupport.created_at >= day_ago)
            ) or 0
            supports_7d = session.scalar(
                select(func.count())
                .select_from(IssueSupport)
                .where(IssueSupport.issue_id == issue.id, IssueSupport.created_at >= week_ago)
            ) or 0
            issue.trending_score = compute_trending_score(
                support_count=issue.support_count,
                supports_24h=supports_24h,
                supports_7d=supports_7d,
                created_at=issue.created_at or now,
            )
            updated += 1
        session.commit()
    return updated


@celery_app.task(name="app.workers.tasks.generate_daily_ai_summary", queue="low")
def generate_daily_ai_summary(target_date: str | None = None) -> dict:
    parsed = date.fromisoformat(target_date) if target_date else None
    with SyncSession() as session:
        summary = daily_summary_generator.generate(session, parsed)
    return summary


@celery_app.task(name="app.workers.tasks.send_notification", queue="high")
def send_notification(
    user_id: str,
    title: str,
    body: str,
    *,
    type: str = "system",
    issue_id: str | None = None,
) -> dict:
    import uuid

    from app.services.notification_service import create_notification

    with SyncSession() as session:
        create_notification(
            session,
            user_id=uuid.UUID(user_id),
            type=type,
            title=title,
            body=body,
            issue_id=uuid.UUID(issue_id) if issue_id else None,
        )
        session.commit()
    return {"user_id": user_id, "title": title, "body": body, "status": "stored"}


@celery_app.task(name="app.workers.tasks.check_sla_breaches", queue="high")
def check_sla_breaches() -> int:
    """Scan open issues and auto-escalate if resolution SLA hours exceeded."""
    from app.core.enums import IssueStatus, TERMINAL_STATUSES, TimelineEventType, Visibility
    from app.models.issue import IssueTimelineEvent

    open_statuses = [s.value for s in IssueStatus if s not in TERMINAL_STATUSES]
    escalated_count = 0
    now = datetime.now(timezone.utc)

    with SyncSession() as session:
        issues = session.execute(
            select(Issue).where(Issue.status.in_(open_statuses))
        ).scalars().all()

        for issue in issues:
            if not issue.created_at:
                continue
            sla_hours = settings.sla_hours_for_severity(int(issue.severity or 3))
            deadline = issue.created_at + timedelta(hours=sla_hours)

            if now > deadline:
                target_status = None
                if issue.status not in {
                    IssueStatus.FORWARDED_STATION_MANAGER.value,
                    IssueStatus.FORWARDED_DIVISION.value,
                    IssueStatus.FORWARDED_ZONE.value,
                }:
                    target_status = IssueStatus.FORWARDED_STATION_MANAGER.value
                elif issue.status == IssueStatus.FORWARDED_STATION_MANAGER.value:
                    target_status = IssueStatus.FORWARDED_DIVISION.value

                if target_status and issue.status != target_status:
                    from_status = issue.status
                    issue.status = target_status
                    session.add(
                        IssueTimelineEvent(
                            issue_id=issue.id,
                            event_type=TimelineEventType.ESCALATED.value,
                            from_status=from_status,
                            to_status=target_status,
                            remarks=f"Automated SLA breach escalation ({sla_hours}h SLA limit exceeded)",
                            visibility=Visibility.PUBLIC.value,
                            metadata_={"automated_sla_escalation": True, "sla_hours": sla_hours},
                        )
                    )
                    escalated_count += 1

        if escalated_count > 0:
            session.commit()
    return escalated_count

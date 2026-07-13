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

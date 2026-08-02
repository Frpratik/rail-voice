from datetime import datetime, timedelta, timezone

import pytest
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.issue import Issue, IssueTimelineEvent
from app.workers.tasks import SyncSession, check_sla_breaches


def test_check_sla_breaches_escalates_expired_issues():
    now = datetime.now(timezone.utc)
    with SyncSession() as session:
        # Fetch an existing public issue
        issue = session.execute(
            select(Issue).where(Issue.is_public.is_(True)).limit(1)
        ).scalar_one_or_none()

        if not issue:
            pytest.skip("No seed issues found for SLA test")

        # Set created_at to 100 hours ago to trigger SLA breach
        issue.created_at = now - timedelta(hours=100)
        issue.status = "submitted"
        session.commit()

        # Run task
        escalated_count = check_sla_breaches()
        assert escalated_count >= 1

        # Verify status updated
        session.refresh(issue)
        assert issue.status == "forwarded_station_manager"

        # Verify timeline event created
        event = session.execute(
            select(IssueTimelineEvent).where(
                IssueTimelineEvent.issue_id == issue.id,
                IssueTimelineEvent.event_type == "escalated",
            )
        ).scalars().first()
        assert event is not None
        assert "SLA breach" in (event.remarks or "")

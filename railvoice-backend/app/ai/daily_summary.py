from __future__ import annotations

from datetime import date, datetime, timezone

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.ai.summarizer import issue_summarizer
from app.core.enums import TERMINAL_STATUSES
from app.models.issue import Issue
from app.models.location import Station


class DailySummaryGenerator:
    def generate(self, session: Session, target_date: date | None = None) -> dict:
        target = target_date or datetime.now(timezone.utc).date()
        day_start = datetime.combine(target, datetime.min.time(), tzinfo=timezone.utc)
        day_end = datetime.combine(target, datetime.max.time(), tzinfo=timezone.utc)

        new_issues = session.scalar(
            select(func.count())
            .select_from(Issue)
            .where(Issue.created_at >= day_start, Issue.created_at <= day_end)
        ) or 0

        resolved = session.scalar(
            select(func.count())
            .select_from(Issue)
            .where(Issue.closed_at >= day_start, Issue.closed_at <= day_end)
        ) or 0

        open_count = session.scalar(
            select(func.count())
            .select_from(Issue)
            .where(Issue.status.notin_([s.value for s in TERMINAL_STATUSES]))
        ) or 0

        top_issues = session.execute(
            select(Issue, Station)
            .join(Station, Issue.station_id == Station.id)
            .where(Issue.is_public.is_(True))
            .order_by(Issue.priority_score.desc())
            .limit(5)
        ).all()

        highlights = []
        for issue, station in top_issues:
            highlights.append(
                {
                    "issue_number": issue.issue_number,
                    "station": station.name,
                    "summary": issue_summarizer.summarize(issue.description, issue.title),
                    "support_count": issue.support_count,
                    "priority_score": float(issue.priority_score or 0),
                }
            )

        narrative = (
            f"On {target.isoformat()}, RailVoice recorded {new_issues} new issues "
            f"across the Western Railway corridor. {resolved} issues were resolved. "
            f"{open_count} issues remain open. "
            f"Top priority: {highlights[0]['summary'] if highlights else 'No open issues'}."
        )

        return {
            "date": target.isoformat(),
            "stats": {
                "new_issues": new_issues,
                "resolved": resolved,
                "open": open_count,
            },
            "top_issues": highlights,
            "narrative": narrative,
        }


daily_summary_generator = DailySummaryGenerator()

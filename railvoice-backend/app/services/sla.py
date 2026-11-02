"""SLA timing and priority scoring. Pure functions so schemas can use them."""

from __future__ import annotations

from datetime import datetime, timedelta, timezone

from app.core.config import settings
from app.core.enums import TERMINAL_STATUSES, IssueStatus

DONE_STATUSES = {s.value for s in TERMINAL_STATUSES} | {
    IssueStatus.COMPLETED.value,
    IssueStatus.VERIFIED_COMPLETE.value,
}


def sla_hours(is_emergency: bool, severity: int | None) -> int:
    if is_emergency:
        return settings.sla_hours_emergency
    # Config lists 1 as the tightest SLA; severity 5 is the most serious.
    return settings.sla_hours_for_severity(6 - (severity or 3))


def sla_due_at(created_at: datetime | None, is_emergency: bool, severity: int | None) -> datetime | None:
    if created_at is None:
        return None
    return created_at + timedelta(hours=sla_hours(is_emergency, severity))


def is_overdue(
    status: str,
    created_at: datetime | None,
    is_emergency: bool,
    severity: int | None,
    now: datetime | None = None,
) -> bool:
    if status in DONE_STATUSES:
        return False
    due = sla_due_at(created_at, is_emergency, severity)
    return bool(due and (now or datetime.now(timezone.utc)) > due)


def priority_score(*, is_emergency: bool, severity: int | None, support_count: int) -> float:
    """Ranks the queue: hazards first, then severity, then how many people are affected."""
    score = (50.0 if is_emergency else 0.0) + (severity or 3) * 5 + min(support_count, 100) * 0.4
    return round(score, 2)

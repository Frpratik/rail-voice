"""Reporting numbers for staff analytics and the public transparency page."""

from __future__ import annotations

from collections import Counter, defaultdict
from datetime import datetime, timedelta, timezone

from sqlalchemy import Select, func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.enums import TERMINAL_STATUSES, IssueStatus
from app.models.issue import Comment, Issue, IssueRating, IssueSupport
from app.models.location import IssueCategory, Station
from app.models.user import User
from app.services.engagement import points_for
from app.services.sla import DONE_STATUSES, is_overdue, sla_due_at

FIXED_STATUSES = {
    IssueStatus.COMPLETED.value,
    IssueStatus.VERIFIED_COMPLETE.value,
    IssueStatus.CLOSED.value,
}
EXCLUDED_STATUSES = {
    IssueStatus.SPAM.value,
    IssueStatus.DUPLICATE_MERGED.value,
    IssueStatus.WITHDRAWN.value,
}
RECURRING_MIN_REPORTS = 3


def _analytics_query() -> Select:
    return (
        select(
            Issue.created_at,
            Issue.resolved_at,
            Issue.status,
            Issue.severity,
            Issue.is_emergency,
            Issue.department,
            Station.name.label("station"),
            Station.code.label("station_code"),
            IssueCategory.name.label("category"),
        )
        .join(Station, Station.id == Issue.station_id)
        .outerjoin(IssueCategory, IssueCategory.id == Issue.category_id)
        .where(Issue.status.notin_(EXCLUDED_STATUSES))
    )


def summarise(rows, *, days: int) -> dict:
    now = datetime.now(timezone.utc)
    start = (now - timedelta(days=days - 1)).date()
    trend = {
        (start + timedelta(days=i)).isoformat(): {"created": 0, "resolved": 0} for i in range(days)
    }
    by_category: Counter[str] = Counter()
    by_department: Counter[str] = Counter()
    stations: dict[str, dict] = {}
    pairs: Counter[tuple[str, str]] = Counter()
    fix_hours: list[float] = []
    met = breached = 0

    for row in rows:
        created = row.created_at.date().isoformat() if row.created_at else None
        if created in trend:
            trend[created]["created"] += 1
        if row.resolved_at:
            resolved = row.resolved_at.date().isoformat()
            if resolved in trend:
                trend[resolved]["resolved"] += 1
            if row.created_at:
                fix_hours.append((row.resolved_at - row.created_at).total_seconds() / 3600)
                due = sla_due_at(row.created_at, row.is_emergency, row.severity)
                if due and row.resolved_at <= due:
                    met += 1
                else:
                    breached += 1

        category = row.category or "Uncategorised"
        by_category[category] += 1
        by_department[row.department or "Unassigned"] += 1
        pairs[(row.station, category)] += 1

        station = stations.setdefault(
            row.station_code,
            {"code": row.station_code, "name": row.station, "total": 0, "open": 0, "overdue": 0},
        )
        station["total"] += 1
        if row.status not in DONE_STATUSES:
            station["open"] += 1
        if is_overdue(row.status, row.created_at, row.is_emergency, row.severity, now):
            station["overdue"] += 1

    resolved_total = met + breached
    return {
        "days": days,
        "total": len(rows),
        "trend": [{"date": day, **values} for day, values in trend.items()],
        "by_category": [{"name": k, "count": v} for k, v in by_category.most_common(10)],
        "by_department": [{"name": k, "count": v} for k, v in by_department.most_common(10)],
        "by_station": sorted(stations.values(), key=lambda s: s["total"], reverse=True)[:10],
        "avg_resolution_hours": round(sum(fix_hours) / len(fix_hours), 1) if fix_hours else None,
        "sla_met_percent": round(met / resolved_total * 100) if resolved_total else None,
        "recurring": [
            {"station": station, "category": category, "count": count}
            for (station, category), count in pairs.most_common(10)
            if count >= RECURRING_MIN_REPORTS
        ],
    }


async def transparency(db: AsyncSession, days: int = 90) -> dict:
    since = datetime.now(timezone.utc) - timedelta(days=days)
    rows = (
        await db.execute(
            _analytics_query().where(Issue.is_public.is_(True), Issue.created_at >= since)
        )
    ).all()
    ratings = await db.execute(
        select(Station.code, func.avg(IssueRating.rating), func.count(IssueRating.id))
        .join(Issue, Issue.id == IssueRating.issue_id)
        .join(Station, Station.id == Issue.station_id)
        .where(IssueRating.created_at >= since)
        .group_by(Station.code)
    )
    rating_by_code = {code: (float(avg), count) for code, avg, count in ratings.all()}

    grouped: dict[str, dict] = defaultdict(
        lambda: {"reports": 0, "open": 0, "fixed": 0, "hours": []}
    )
    for row in rows:
        entry = grouped[row.station_code]
        entry["code"] = row.station_code
        entry["name"] = row.station
        entry["reports"] += 1
        if row.status in FIXED_STATUSES:
            entry["fixed"] += 1
        elif row.status not in {s.value for s in TERMINAL_STATUSES}:
            entry["open"] += 1
        if row.resolved_at and row.created_at:
            entry["hours"].append((row.resolved_at - row.created_at).total_seconds() / 3600)

    stations = []
    for entry in grouped.values():
        hours = entry.pop("hours")
        rating = rating_by_code.get(entry["code"])
        stations.append(
            {
                **entry,
                "fix_rate": round(entry["fixed"] / entry["reports"] * 100),
                "avg_fix_hours": round(sum(hours) / len(hours), 1) if hours else None,
                "avg_rating": round(rating[0], 1) if rating else None,
            }
        )
    stations.sort(key=lambda s: (s["fix_rate"], s["reports"]), reverse=True)

    total = len(rows)
    fixed = sum(s["fixed"] for s in stations)
    return {
        "days": days,
        "total_reports": total,
        "open": sum(s["open"] for s in stations),
        "fixed": fixed,
        "fix_rate": round(fixed / total * 100) if total else None,
        "stations": stations,
    }


async def passenger_leaderboard(db: AsyncSession, limit: int = 20) -> list[dict]:
    reports = await db.execute(
        select(Issue.creator_id, func.count(Issue.id))
        .where(Issue.status != IssueStatus.SPAM.value, Issue.creator_id.is_not(None))
        .group_by(Issue.creator_id)
    )
    fixed = await db.execute(
        select(Issue.creator_id, func.count(Issue.id))
        .where(Issue.status == IssueStatus.CLOSED.value, Issue.creator_id.is_not(None))
        .group_by(Issue.creator_id)
    )
    backed = await db.execute(
        select(IssueSupport.user_id, func.count(IssueSupport.id))
        .join(Issue, Issue.id == IssueSupport.issue_id)
        .where(Issue.creator_id != IssueSupport.user_id)
        .group_by(IssueSupport.user_id)
    )
    comments = await db.execute(
        select(Comment.user_id, func.count(Comment.id))
        .where(Comment.is_hidden.is_(False))
        .group_by(Comment.user_id)
    )
    report_map = dict(reports.all())
    fixed_map = dict(fixed.all())
    backed_map = dict(backed.all())
    comment_map = dict(comments.all())

    ids = set(report_map) | set(backed_map) | set(comment_map)
    if not ids:
        return []
    users = await db.execute(
        select(User.id, User.display_name).where(
            User.id.in_(ids), User.is_anonymous.is_(False), User.deleted_at.is_(None)
        )
    )
    board = [
        {
            "display_name": name,
            "reports": report_map.get(user_id, 0),
            "points": points_for(
                report_map.get(user_id, 0),
                backed_map.get(user_id, 0),
                comment_map.get(user_id, 0),
                fixed_map.get(user_id, 0),
            ),
        }
        for user_id, name in users.all()
    ]
    board.sort(key=lambda r: r["points"], reverse=True)
    return board[:limit]

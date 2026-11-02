"""Generative-AI endpoints. All return 503 when AI is off, so the web app can hide or skip them."""

from __future__ import annotations

import uuid
from typing import Annotated

from fastapi import APIRouter, Depends, File, HTTPException, UploadFile, status
from pydantic import BaseModel, Field
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.ai import reporting, staff
from app.ai.client import AIUnavailable, ai_enabled
from app.core.config import settings
from app.core.deps import get_current_user, get_db, require_official
from app.models.issue import Issue
from app.services.scope import enforce_issue_location_scope
from app.models.location import IssueCategory, Station
from app.models.user import User
from app.schemas.common import Envelope, Meta

router = APIRouter(prefix="/ai", tags=["AI"])


def _unavailable(exc: AIUnavailable) -> HTTPException:
    return HTTPException(status_code=status.HTTP_503_SERVICE_UNAVAILABLE, detail=str(exc))


class DraftRequest(BaseModel):
    note: str = Field(..., min_length=5, max_length=2000)
    station_id: str | None = None


@router.get("/status")
async def ai_status() -> Envelope[dict]:
    return Envelope(
        data={
            "enabled": ai_enabled(),
            "model": settings.ai_model if ai_enabled() and settings.ai_provider == "claude" else None,
        },
        meta=Meta(),
    )


@router.post("/draft-report")
async def draft_report(
    body: DraftRequest,
    db: Annotated[AsyncSession, Depends(get_db)],
    _: Annotated[User, Depends(get_current_user)],
) -> Envelope[dict]:
    categories = dict(
        (
            await db.execute(
                select(IssueCategory.code, IssueCategory.name).where(IssueCategory.is_active.is_(True))
            )
        ).all()
    )
    station_name = None
    if body.station_id:
        station = await db.get(Station, body.station_id)
        station_name = station.name if station else None
    try:
        draft = await reporting.draft_report(body.note, station_name=station_name, categories=categories)
    except AIUnavailable as exc:
        raise _unavailable(exc) from exc
    return Envelope(data=draft, meta=Meta())


class ReplyRequest(BaseModel):
    issue_id: str
    notes: str = Field(..., min_length=2, max_length=1000)
    new_status: str | None = None


@router.post("/suggest-reply")
async def suggest_reply(
    body: ReplyRequest,
    db: Annotated[AsyncSession, Depends(get_db)],
    officer: Annotated[User, Depends(require_official)],
) -> Envelope[dict]:
    issue = await db.get(Issue, body.issue_id)
    if not issue:
        raise HTTPException(status_code=404, detail="Issue not found")
    enforce_issue_location_scope(officer, issue)
    try:
        reply = await staff.suggest_reply(
            report=f"{issue.title or ''}\n{issue.description}",
            notes=body.notes,
            new_status=body.new_status,
        )
    except AIUnavailable as exc:
        raise _unavailable(exc) from exc
    return Envelope(data=reply, meta=Meta())


@router.get("/briefing")
async def daily_briefing(
    db: Annotated[AsyncSession, Depends(get_db)],
    officer: Annotated[User, Depends(require_official)],
    refresh: bool = False,
) -> Envelope[dict]:
    from datetime import datetime, timedelta, timezone

    from app.ai import cache
    from app.api.v1.admin import _scoped_issues
    from app.core.enums import TERMINAL_STATUSES
    from app.services.scope import official_location_scopes
    from app.services.sla import DONE_STATUSES, is_overdue

    scopes = official_location_scopes(officer)
    key = f"briefing:{officer.id}:{datetime.now(timezone.utc):%Y-%m-%d-%H}"
    if not refresh and (cached := cache.get(key)):
        return Envelope(data=cached, meta=Meta())

    now = datetime.now(timezone.utc)
    rows = (
        await db.execute(
            _scoped_issues(
                select(Issue)
                .where(
                    Issue.is_public.is_(True),
                    Issue.status.notin_(list(DONE_STATUSES | {s.value for s in TERMINAL_STATUSES})),
                )
                .order_by(Issue.priority_score.desc())
                .limit(40),
                officer,
            )
        )
    ).scalars().all()
    reports = [
        {
            "number": i.issue_number,
            "station": i.station.name if i.station else "",
            "category": i.category.name if i.category else "Other",
            "status": i.status.replace("_", " "),
            "age_hours": int((now - i.created_at).total_seconds() // 3600) if i.created_at else 0,
            "support": i.support_count,
            "emergency": i.is_emergency,
            "overdue": is_overdue(i.status, i.created_at, i.is_emergency, i.severity, now),
            "title": (i.title or i.description)[:120],
        }
        for i in rows
    ]
    since = now - timedelta(hours=24)
    new_24h = await db.scalar(
        _scoped_issues(select(func.count()).select_from(Issue).where(Issue.created_at >= since), officer)
    )
    resolved_24h = await db.scalar(
        _scoped_issues(select(func.count()).select_from(Issue).where(Issue.resolved_at >= since), officer)
    )
    try:
        brief = await staff.briefing(
            scope_label="all Western line stations" if scopes is None else "your assigned stations",
            reports=reports,
            new_24h=new_24h or 0,
            resolved_24h=resolved_24h or 0,
        )
    except AIUnavailable as exc:
        raise _unavailable(exc) from exc
    data = {**brief, "generated_at": now.isoformat(), "open_count": len(reports)}
    cache.put(key, data, hours=1)
    return Envelope(data=data, meta=Meta())


def _public_row(issue: Issue, now) -> dict:
    return {
        "number": issue.issue_number,
        "station": issue.station.name if issue.station else "",
        "category": issue.category.name if issue.category else "Other",
        "status": issue.status.replace("_", " "),
        "age_days": (now - issue.created_at).days if issue.created_at else 0,
        "support": issue.support_count,
        "title": (issue.title or issue.description)[:120],
    }


def _open_public():
    from app.core.enums import TERMINAL_STATUSES
    from app.services.sla import DONE_STATUSES

    return select(Issue).where(
        Issue.is_public.is_(True),
        Issue.merged_into_id.is_(None),
        Issue.status.notin_(list(DONE_STATUSES | {s.value for s in TERMINAL_STATUSES})),
    )


class AskRequest(BaseModel):
    question: str = Field(..., min_length=3, max_length=500)
    station_id: str | None = None


@router.post("/ask")
async def ask(
    body: AskRequest,
    db: Annotated[AsyncSession, Depends(get_db)],
    _: Annotated[User, Depends(get_current_user)],
) -> Envelope[dict]:
    from datetime import datetime, timezone

    from app.ai import assistant

    now = datetime.now(timezone.utc)
    query = _open_public()
    station = await db.get(Station, body.station_id) if body.station_id else None
    if station:
        query = query.where(Issue.station_id == station.id)
    rows = (await db.execute(query.order_by(Issue.priority_score.desc()).limit(40))).scalars().all()
    try:
        answer = await assistant.ask(
            body.question,
            station_name=station.name if station else None,
            reports=[_public_row(i, now) for i in rows],
        )
    except AIUnavailable as exc:
        raise _unavailable(exc) from exc
    by_number = {i.issue_number: i for i in rows}
    answer["issues"] = [
        {"id": str(by_number[n].id), "issue_number": n, "title": by_number[n].title or by_number[n].description[:80]}
        for n in answer.pop("issue_numbers")
    ]
    return Envelope(data=answer, meta=Meta())


@router.get("/translate/{issue_id}")
async def translate_issue(
    issue_id: uuid.UUID,
    db: Annotated[AsyncSession, Depends(get_db)],
    lang: str = "en",
) -> Envelope[dict]:
    from app.ai import assistant, cache

    if lang not in assistant.LANGUAGE_NAMES:
        raise HTTPException(status_code=400, detail="Language must be en, hi, mr or gu")
    issue = await db.get(Issue, issue_id)
    if not issue or not issue.is_public:
        raise HTTPException(status_code=404, detail="Issue not found")
    stamp = int(issue.updated_at.timestamp()) if issue.updated_at else 0
    key = f"translate:{issue.id}:{lang}:{stamp}"
    if not (result := cache.get(key)):
        try:
            result = await assistant.translate(
                title=issue.title or "", description=issue.description, target=lang
            )
        except AIUnavailable as exc:
            raise _unavailable(exc) from exc
        cache.put(key, result)
    return Envelope(data={**result, "lang": lang}, meta=Meta())


@router.get("/station-summary/{station_id}")
async def station_summary(
    station_id: uuid.UUID,
    db: Annotated[AsyncSession, Depends(get_db)],
) -> Envelope[dict]:
    from datetime import datetime, timedelta, timezone

    from app.ai import assistant, cache

    station = await db.get(Station, station_id)
    if not station:
        raise HTTPException(status_code=404, detail="Station not found")
    now = datetime.now(timezone.utc)
    key = f"station:{station.id}:{now:%Y-%m-%d}-{now.hour // 6}"
    if cached := cache.get(key):
        return Envelope(data=cached, meta=Meta())
    open_rows = (
        await db.execute(
            _open_public().where(Issue.station_id == station.id).order_by(Issue.priority_score.desc()).limit(30)
        )
    ).scalars().all()
    fixed_rows = (
        await db.execute(
            select(Issue)
            .where(
                Issue.station_id == station.id,
                Issue.is_public.is_(True),
                Issue.resolved_at >= now - timedelta(days=30),
            )
            .order_by(Issue.resolved_at.desc())
            .limit(15)
        )
    ).scalars().all()
    try:
        summary = await assistant.station_summary(
            station_name=station.name,
            open_reports=[_public_row(i, now) for i in open_rows],
            fixed_recently=[_public_row(i, now) for i in fixed_rows],
        )
    except AIUnavailable as exc:
        raise _unavailable(exc) from exc
    data = {**summary, "generated_at": now.isoformat(), "open_count": len(open_rows)}
    cache.put(key, data, hours=6)
    return Envelope(data=data, meta=Meta())


@router.post("/analyze-photo")
async def analyze_photo(
    db: Annotated[AsyncSession, Depends(get_db)],
    _: Annotated[User, Depends(get_current_user)],
    file: UploadFile = File(...),
) -> Envelope[dict]:
    from app.services.storage import storage_service

    data = await file.read()
    if len(data) > 5 * 1024 * 1024:
        raise HTTPException(status_code=400, detail="Photo must be under 5MB")
    try:
        mime = storage_service.validate_image_bytes(data)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    if mime == "image/gif":
        raise HTTPException(status_code=400, detail="Please use a JPEG, PNG or WebP photo")
    data = storage_service.strip_metadata(data, mime)
    categories = dict(
        (
            await db.execute(
                select(IssueCategory.code, IssueCategory.name).where(IssueCategory.is_active.is_(True))
            )
        ).all()
    )
    try:
        result = await reporting.analyze_photo(data, mime, categories=categories)
    except AIUnavailable as exc:
        raise _unavailable(exc) from exc
    return Envelope(data=result, meta=Meta())


@router.post("/triage/{issue_id}")
async def triage(
    issue_id: uuid.UUID,
    db: Annotated[AsyncSession, Depends(get_db)],
    officer: Annotated[User, Depends(require_official)],
) -> Envelope[dict]:
    issue = await db.get(Issue, issue_id)
    if not issue:
        raise HTTPException(status_code=404, detail="Issue not found")
    enforce_issue_location_scope(officer, issue)
    try:
        result = await staff.triage(
            report=f"{issue.title or ''}\n{issue.description}",
            category=issue.category.name if issue.category else "Other",
            support=issue.support_count,
            is_emergency=issue.is_emergency,
        )
    except AIUnavailable as exc:
        raise _unavailable(exc) from exc
    return Envelope(data=result, meta=Meta())


@router.get("/recurring")
async def recurring_problems(
    db: Annotated[AsyncSession, Depends(get_db)],
    officer: Annotated[User, Depends(require_official)],
) -> Envelope[dict]:
    """Station and problem-type pairs reported 3+ times in 90 days, with an AI explanation of each."""
    from collections import defaultdict
    from datetime import datetime, timedelta, timezone

    from app.ai import cache
    from app.api.v1.admin import _scoped_issues

    now = datetime.now(timezone.utc)
    key = f"recurring:{officer.id}:{now:%Y-%m-%d}"
    if cached := cache.get(key):
        return Envelope(data=cached, meta=Meta())
    rows = (
        await db.execute(
            _scoped_issues(
                select(Issue)
                .where(Issue.created_at >= now - timedelta(days=90), Issue.merged_into_id.is_(None))
                .order_by(Issue.created_at.desc())
                .limit(500),
                officer,
            )
        )
    ).scalars().all()
    grouped: dict[tuple, list[Issue]] = defaultdict(list)
    for issue in rows:
        grouped[(issue.station_id, issue.category_id)].append(issue)
    top = sorted((g for g in grouped.values() if len(g) >= 3), key=len, reverse=True)[:5]
    groups = [
        {
            "key": f"G{n + 1}",
            "station": g[0].station.name if g[0].station else "",
            "category": g[0].category.name if g[0].category else "Other",
            "count": len(g),
            "reports": [
                {
                    "date": f"{i.created_at:%Y-%m-%d %a %H:%M}" if i.created_at else "",
                    "status": i.status.replace("_", " "),
                    "text": f"{i.title or ''} {i.description}"[:160],
                    "number": i.issue_number,
                    "id": str(i.id),
                }
                for i in g[:8]
            ],
        }
        for n, g in enumerate(top)
    ]
    explained: dict[str, dict] = {}
    if groups:
        try:
            explained = {e["key"]: e for e in await staff.explain_recurring(groups)}
        except AIUnavailable as exc:
            raise _unavailable(exc) from exc
    items = [
        {
            "station": g["station"],
            "category": g["category"],
            "count": g["count"],
            "reports": [{"id": r["id"], "issue_number": r["number"]} for r in g["reports"]],
            "pattern": explained.get(g["key"], {}).get("pattern", ""),
            "likely_cause": explained.get(g["key"], {}).get("likely_cause", ""),
            "fix": explained.get(g["key"], {}).get("fix", ""),
        }
        for g in groups
    ]
    data = {"items": items, "generated_at": now.isoformat()}
    cache.put(key, data, hours=24)
    return Envelope(data=data, meta=Meta())


@router.get("/monthly-report")
async def monthly_report(
    db: Annotated[AsyncSession, Depends(get_db)],
    officer: Annotated[User, Depends(require_official)],
    month: str | None = None,
) -> Envelope[dict]:
    """An AI-written monthly summary for senior officials. `month` is YYYY-MM; default is last month."""
    from collections import Counter
    from datetime import datetime, timezone

    from app.ai import cache
    from app.api.v1.admin import _scoped_issues
    from app.core.enums import TERMINAL_STATUSES
    from app.services.scope import official_location_scopes
    from app.services.sla import DONE_STATUSES

    now = datetime.now(timezone.utc)
    if month:
        try:
            start = datetime.strptime(month, "%Y-%m").replace(tzinfo=timezone.utc)
        except ValueError as exc:
            raise HTTPException(status_code=400, detail="Month must look like 2026-10") from exc
    else:
        first = now.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
        start = (first.replace(year=first.year - 1, month=12) if first.month == 1 else first.replace(month=first.month - 1))
    end = start.replace(year=start.year + 1, month=1) if start.month == 12 else start.replace(month=start.month + 1)
    if start > now:
        raise HTTPException(status_code=400, detail="That month hasn't started yet")
    key = f"monthly:{officer.id}:{start:%Y-%m}"
    if cached := cache.get(key):
        return Envelope(data=cached, meta=Meta())

    created = (
        await db.execute(
            _scoped_issues(select(Issue).where(Issue.created_at >= start, Issue.created_at < end), officer)
        )
    ).scalars().all()
    resolved = (
        await db.execute(
            _scoped_issues(select(Issue).where(Issue.resolved_at >= start, Issue.resolved_at < end), officer)
        )
    ).scalars().all()
    done = DONE_STATUSES | {s.value for s in TERMINAL_STATUSES}
    fix_hours = sorted(
        (i.resolved_at - i.created_at).total_seconds() / 3600 for i in resolved if i.created_at and i.resolved_at
    )
    figures = {
        "New reports": len(created),
        "Reports fixed this month": len(resolved),
        "Reports from this month still open": sum(1 for i in created if i.status not in done),
        "Emergencies reported": sum(1 for i in created if i.is_emergency),
        "Median hours to fix": round(fix_hours[len(fix_hours) // 2], 1) if fix_hours else "no fixes",
        "Passenger backings": sum(i.support_count for i in created),
        "Top problem types": ", ".join(
            f"{name} ({n})" for name, n in Counter(i.category.name if i.category else "Other" for i in created).most_common(5)
        ) or "none",
        "Stations with most reports": ", ".join(
            f"{name} ({n})" for name, n in Counter(i.station.name if i.station else "" for i in created).most_common(5)
        ) or "none",
    }
    notable = [
        f"{i.issue_number} | {i.station.name if i.station else ''} | {i.status.replace('_', ' ')} | "
        f"backed by {i.support_count} | {(i.title or i.description)[:100]}"
        for i in sorted(created, key=lambda i: (i.is_emergency, i.support_count), reverse=True)[:8]
    ]
    scopes = official_location_scopes(officer)
    try:
        report = await staff.monthly_report(
            month_label=f"{start:%B %Y}",
            scope_label="all Western line stations" if scopes is None else "the officer's assigned stations",
            figures=figures,
            notable=notable,
        )
    except AIUnavailable as exc:
        raise _unavailable(exc) from exc
    data = {**report, "month": f"{start:%Y-%m}", "month_label": f"{start:%B %Y}", "figures": figures}
    if end <= now:  # a finished month won't change, so keep it longer
        cache.put(key, data, hours=24 * 7)
    else:
        cache.put(key, data, hours=1)
    return Envelope(data=data, meta=Meta())


@router.post("/fix-check/{issue_id}")
async def fix_check(
    issue_id: uuid.UUID,
    db: Annotated[AsyncSession, Depends(get_db)],
    officer: Annotated[User, Depends(require_official)],
) -> Envelope[dict]:
    """Compare the passenger's photos with the latest proof-of-fix photo."""
    from app.ai.client import Image
    from app.models.issue import IssuePhoto
    from app.services.storage import storage_service

    issue = await db.get(Issue, issue_id)
    if not issue:
        raise HTTPException(status_code=404, detail="Issue not found")
    enforce_issue_location_scope(officer, issue)
    photos = (
        await db.execute(
            select(IssuePhoto)
            .where(IssuePhoto.issue_id == issue.id, IssuePhoto.mime_type != "image/gif")
            .order_by(IssuePhoto.created_at)
        )
    ).scalars().all()
    before = [p for p in photos if (p.kind or "evidence") == "evidence"][:2]
    after = [p for p in photos if p.kind == "resolution"]
    if not before or not after:
        raise HTTPException(status_code=400, detail="Needs a passenger photo and a proof-of-fix photo")
    try:
        images = [Image(data=await storage_service.load_bytes(p.storage_key), media_type=p.mime_type) for p in [*before, after[-1]]]
    except (OSError, ValueError) as exc:
        raise HTTPException(status_code=404, detail="Photo file not found") from exc
    try:
        result = await staff.fix_check(
            report=f"{issue.title or ''}\n{issue.description}", before=images[:-1], after=images[-1]
        )
    except AIUnavailable as exc:
        raise _unavailable(exc) from exc
    return Envelope(data=result, meta=Meta())

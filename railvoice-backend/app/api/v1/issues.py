import uuid
from datetime import datetime, timedelta, timezone
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.core.deps import get_current_user, get_current_user_optional, get_db, get_reporter_user
from app.core.enums import TERMINAL_STATUSES
from app.models.issue import Comment, Issue, IssueFlag, IssueFollower, IssueRating, IssueSupport
from app.models.location import IssueCategory, Station, Zone
from app.models.user import User
from app.schemas.common import (
    CategoryOut,
    ConfirmResolutionRequest,
    Envelope,
    FlagRequest,
    IssueCreateRequest,
    IssueDetailOut,
    Meta,
    StationOut,
    SupportResponse,
    WithdrawRequest,
)
from app.schemas.mappers import issue_detail_to_out, issue_to_out, station_to_out
from app.services import engagement, issue_actions
from app.services.issue_service import issue_service

router = APIRouter(tags=["Issues", "Stations"])


@router.get("/categories", response_model=Envelope[list[CategoryOut]])
async def list_categories(
    db: Annotated[AsyncSession, Depends(get_db)],
) -> Envelope[list[CategoryOut]]:
    result = await db.execute(
        select(IssueCategory).where(IssueCategory.is_active.is_(True)).order_by(IssueCategory.sort_order)
    )
    categories = result.scalars().all()
    return Envelope(data=[CategoryOut.model_validate(c) for c in categories], meta=Meta())


@router.get("/stations", response_model=Envelope[list[StationOut]])
async def list_stations(
    db: Annotated[AsyncSession, Depends(get_db)],
    zone_code: str | None = Query(None),
    search: str | None = Query(None),
) -> Envelope[list[StationOut]]:
    query = select(Station).options(selectinload(Station.division)).where(Station.is_active.is_(True))
    if zone_code:
        query = query.join(Zone, Station.zone_id == Zone.id).where(Zone.code == zone_code.upper())
    if search:
        query = query.where(Station.name.ilike(f"%{search}%"))
    query = query.order_by(Station.sequence_order)
    result = await db.execute(query)
    stations = result.scalars().all()
    counts = dict(
        (
            await db.execute(
                select(Issue.station_id, func.count(Issue.id))
                .where(
                    Issue.is_public.is_(True),
                    Issue.status.notin_([s.value for s in TERMINAL_STATUSES]),
                )
                .group_by(Issue.station_id)
            )
        ).all()
    )
    data = [station_to_out(s, counts.get(s.id, 0)) for s in stations]
    return Envelope(data=data, meta=Meta())


@router.get("/stations/{station_code}", response_model=Envelope[StationOut])
async def get_station(
    station_code: str,
    db: Annotated[AsyncSession, Depends(get_db)],
) -> Envelope[StationOut]:
    result = await db.execute(
        select(Station)
        .options(selectinload(Station.division))
        .where(Station.code == station_code.upper())
    )
    station = result.scalar_one_or_none()
    if not station:
        raise HTTPException(status_code=404, detail="Station not found")
    open_count_result = await db.execute(
        select(func.count())
        .select_from(Issue)
        .where(
            Issue.station_id == station.id,
            Issue.status.in_(["submitted", "under_review", "verified", "assigned", "action_started", "work_in_progress"]),
        )
    )
    return Envelope(data=station_to_out(station, open_count_result.scalar() or 0), meta=Meta())


@router.post("/issues", status_code=status.HTTP_201_CREATED)
async def create_issue(
    body: IssueCreateRequest,
    db: Annotated[AsyncSession, Depends(get_db)],
    user: Annotated[User, Depends(get_current_user)],
) -> Envelope[dict]:
    category_id = body.category_id
    if not category_id and body.category_code:
        cat_result = await db.execute(
            select(IssueCategory).where(IssueCategory.code == body.category_code.lower())
        )
        found_cat = cat_result.scalar_one_or_none()
        if found_cat:
            category_id = found_cat.id

    try:
        issue = await issue_service.create_issue(
            db,
            creator=user,
            station_id=body.station_id,
            category_id=category_id,
            description=body.description,
            title=body.title,
            platform_id=body.platform_id,
            train_number=body.train_number,
            coach_number=body.coach_number,
            pnr_number=body.pnr_number,
            berth_number=body.berth_number,
            upcoming_station_code=body.upcoming_station_code,
            is_emergency=getattr(body, "is_emergency", False),
            latitude=body.latitude,
            longitude=body.longitude,
        )
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)) from exc

    station_result = await db.execute(select(Station).where(Station.id == issue.station_id))
    station = station_result.scalar_one_or_none()
    category = None
    if issue.category_id:
        category_result = await db.execute(
            select(IssueCategory).where(IssueCategory.id == issue.category_id)
        )
        category = category_result.scalar_one_or_none()

    return Envelope(
        data={
            "issue": issue_to_out(
                issue,
                station=station,
                category=category,
                creator=user,
            ).model_dump(mode="json"),
        },
        meta=Meta(),
    )


@router.get("/issues/mine")
async def list_my_issues(
    db: Annotated[AsyncSession, Depends(get_db)],
    user: Annotated[User, Depends(get_reporter_user)],
    limit: int = Query(50, ge=1, le=100),
) -> Envelope[dict]:
    query = (
        select(Issue)
        .options(
            selectinload(Issue.station),
            selectinload(Issue.category),
            selectinload(Issue.photos),
        )
        .where(Issue.creator_id == user.id)
        .order_by(Issue.created_at.desc())
        .limit(limit)
    )
    result = await db.execute(query)
    issues = result.scalars().all()
    total = await db.scalar(
        select(func.count()).select_from(Issue).where(Issue.creator_id == user.id)
    )
    return Envelope(
        data={
            "items": [issue_to_out(issue).model_dump(mode="json") for issue in issues],
            "pagination": {
                "next_cursor": None,
                "has_more": (total or 0) > len(issues),
                "total_count": total or 0,
            },
        },
        meta=Meta(),
    )


@router.get("/issues/similar")
async def similar_issues(
    db: Annotated[AsyncSession, Depends(get_db)],
    station_id: uuid.UUID,
    category_code: str | None = Query(None),
    q: str | None = Query(None, max_length=500),
    limit: int = Query(5, ge=1, le=10),
) -> Envelope[dict]:
    """Open reports at this station that look like the one being written."""
    issues = await issue_actions.find_similar_issues(
        db, station_id=station_id, category_code=category_code, text=q, limit=limit
    )
    return Envelope(
        data={"items": [issue_to_out(i).model_dump(mode="json") for i in issues]},
        meta=Meta(),
    )


@router.get("/issues/{issue_id}", response_model=Envelope[IssueDetailOut])
async def get_issue(
    issue_id: uuid.UUID,
    db: Annotated[AsyncSession, Depends(get_db)],
    user: Annotated[User | None, Depends(get_current_user_optional)],
) -> Envelope[IssueDetailOut]:
    issue = await issue_service.get_issue_detail(db, issue_id)
    if not issue or (not issue.is_public and issue.creator_id != getattr(user, "id", None)):
        raise HTTPException(status_code=404, detail="Issue not found")
    detail = issue_detail_to_out(issue)
    is_creator = bool(user and issue.creator_id == user.id)
    supported = False
    flagged = False
    following = False
    my_rating = None
    if user:
        supported = bool(
            await db.scalar(
                select(func.count())
                .select_from(IssueSupport)
                .where(IssueSupport.issue_id == issue.id, IssueSupport.user_id == user.id)
            )
        )
        flagged = bool(
            await db.scalar(
                select(func.count())
                .select_from(IssueFlag)
                .where(
                    IssueFlag.issue_id == issue.id,
                    IssueFlag.user_id == user.id,
                    IssueFlag.comment_id.is_(None),
                )
            )
        )
    if user:
        following = bool(
            await db.scalar(
                select(func.count())
                .select_from(IssueFollower)
                .where(IssueFollower.issue_id == issue.id, IssueFollower.user_id == user.id)
            )
        )
        my_rating = await db.scalar(
            select(IssueRating.rating).where(
                IssueRating.issue_id == issue.id, IssueRating.user_id == user.id
            )
        )
    detail.viewer = {
        "signed_in": bool(user and not user.is_anonymous),
        "is_creator": is_creator,
        "supported": supported,
        "flagged": flagged,
        "can_withdraw": is_creator and issue.status in issue_actions.WITHDRAWABLE,
        "can_confirm": is_creator and issue.status in issue_actions.CONFIRMABLE,
        "following": following,
        "my_rating": my_rating,
        "can_rate": (is_creator or supported) and issue.status in engagement.RATEABLE,
        "rating": await engagement.rating_summary(db, issue.id),
    }
    return Envelope(data=detail, meta=Meta())


@router.get("/issues")
async def list_issues(
    db: Annotated[AsyncSession, Depends(get_db)],
    station_code: str | None = Query(None),
    status: str | None = Query(None),
    category_code: str | None = Query(None),
    open_only: bool = Query(False),
    since_days: int | None = Query(None, ge=1, le=365),
    sort: str = Query("most_supported"),
    limit: int = Query(20, ge=1, le=100),
) -> Envelope[dict]:
    query = (
        select(Issue)
        .options(selectinload(Issue.station), selectinload(Issue.category))
        .where(Issue.is_public.is_(True))
    )
    if station_code:
        query = query.join(Issue.station).where(Station.code == station_code.upper())
    if status:
        query = query.where(Issue.status == status)
    if category_code:
        query = query.join(Issue.category).where(IssueCategory.code == category_code.lower())
    if open_only:
        query = query.where(Issue.status.notin_([s.value for s in TERMINAL_STATUSES]))
    if since_days:
        query = query.where(Issue.created_at >= datetime.now(timezone.utc) - timedelta(days=since_days))

    if sort == "newest":
        query = query.order_by(Issue.created_at.desc())
    elif sort == "urgent":
        query = query.order_by(Issue.priority_score.desc(), Issue.created_at.desc())
    else:
        query = query.order_by(Issue.support_count.desc(), Issue.created_at.desc())

    query = query.limit(limit)
    result = await db.execute(query)
    issues = result.scalars().all()
    return Envelope(
        data={
            "items": [issue_to_out(i).model_dump(mode="json") for i in issues],
            "pagination": {"next_cursor": None, "has_more": False, "total_count": len(issues)},
        },
        meta=Meta(),
    )


@router.post("/issues/{issue_id}/support", response_model=Envelope[SupportResponse])
async def support_issue(
    issue_id: uuid.UUID,
    db: Annotated[AsyncSession, Depends(get_db)],
    user: Annotated[User, Depends(get_reporter_user)],
) -> Envelope[SupportResponse]:
    try:
        await issue_service.support_issue(db, user, issue_id)
        issue = await db.get(Issue, issue_id)
    except ValueError as exc:
        msg = str(exc)
        code = status.HTTP_409_CONFLICT if "Already" in msg else status.HTTP_400_BAD_REQUEST
        raise HTTPException(status_code=code, detail=msg) from exc

    return Envelope(
        data=SupportResponse(
            issue_id=issue_id,
            support_count=issue.support_count if issue else 0,
            message="Thank you for supporting this issue",
        ),
        meta=Meta(),
    )


async def _load_issue(db: AsyncSession, issue_id: uuid.UUID) -> Issue:
    issue = await db.get(Issue, issue_id)
    if not issue:
        raise HTTPException(status_code=404, detail="Issue not found")
    return issue


def _as_http_error(exc: Exception) -> HTTPException:
    if isinstance(exc, PermissionError):
        return HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=str(exc))
    return HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc))


@router.post("/issues/{issue_id}/withdraw")
async def withdraw_issue(
    issue_id: uuid.UUID,
    body: WithdrawRequest,
    db: Annotated[AsyncSession, Depends(get_db)],
    user: Annotated[User, Depends(get_reporter_user)],
) -> Envelope[dict]:
    issue = await _load_issue(db, issue_id)
    try:
        await issue_actions.withdraw_issue(db, issue, user, body.reason)
    except (PermissionError, ValueError) as exc:
        raise _as_http_error(exc) from exc
    await db.flush()
    return Envelope(data={"status": issue.status}, meta=Meta())


@router.post("/issues/{issue_id}/confirm")
async def confirm_issue_resolution(
    issue_id: uuid.UUID,
    body: ConfirmResolutionRequest,
    db: Annotated[AsyncSession, Depends(get_db)],
    user: Annotated[User, Depends(get_reporter_user)],
) -> Envelope[dict]:
    issue = await _load_issue(db, issue_id)
    try:
        await issue_actions.confirm_resolution(db, issue, user, fixed=body.fixed, remarks=body.remarks)
    except (PermissionError, ValueError) as exc:
        raise _as_http_error(exc) from exc
    await db.flush()
    return Envelope(data={"status": issue.status}, meta=Meta())


@router.post("/issues/{issue_id}/flag", status_code=status.HTTP_201_CREATED)
async def flag_issue(
    issue_id: uuid.UUID,
    body: FlagRequest,
    db: Annotated[AsyncSession, Depends(get_db)],
    user: Annotated[User, Depends(get_reporter_user)],
) -> Envelope[dict]:
    issue = await _load_issue(db, issue_id)
    if not issue.is_public:
        raise HTTPException(status_code=404, detail="Issue not found")
    try:
        await issue_actions.flag_target(
            db, user=user, issue=issue, comment=None, reason=body.reason, note=body.note
        )
    except ValueError as exc:
        raise _as_http_error(exc) from exc
    return Envelope(data={"flagged": True}, meta=Meta())


@router.post("/comments/{comment_id}/flag", status_code=status.HTTP_201_CREATED)
async def flag_comment(
    comment_id: uuid.UUID,
    body: FlagRequest,
    db: Annotated[AsyncSession, Depends(get_db)],
    user: Annotated[User, Depends(get_reporter_user)],
) -> Envelope[dict]:
    comment = await db.get(Comment, comment_id)
    if not comment or comment.is_hidden:
        raise HTTPException(status_code=404, detail="Comment not found")
    issue = await _load_issue(db, comment.issue_id)
    try:
        await issue_actions.flag_target(
            db, user=user, issue=issue, comment=comment, reason=body.reason, note=body.note
        )
    except ValueError as exc:
        raise _as_http_error(exc) from exc
    return Envelope(data={"flagged": True}, meta=Meta())

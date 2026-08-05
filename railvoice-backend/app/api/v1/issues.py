import uuid
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Query, status, File, UploadFile
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.services.visual_resolver import VisualResolverService

from app.ai.duplicate import effective_duplicate_threshold
from app.core.deps import get_db, get_reporter_user
from app.core.enums import DUPLICATE_SEARCH_EXCLUDED
from app.models.issue import Issue
from app.models.location import Division, IssueCategory, Station, Zone
from app.models.user import User
from app.schemas.common import (
    DuplicateCheckRequest,
    DuplicateCheckResponse,
    Envelope,
    IssueCreateRequest,
    IssueDetailOut,
    Meta,
    SimilarIssueOut,
    StationOut,
    SupportResponse,
)
from app.schemas.mappers import issue_detail_to_out, issue_to_out, similar_issue_to_out, station_to_out
from app.ai.duplicate import duplicate_detection_service
from app.services.issue_service import DuplicateFoundError, issue_service

router = APIRouter(tags=["Issues", "Stations"])


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
    data = [station_to_out(s) for s in stations]
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
            Issue.status.notin_([s.value for s in DUPLICATE_SEARCH_EXCLUDED]),
        )
    )
    return Envelope(data=station_to_out(station, open_count_result.scalar() or 0), meta=Meta())


@router.post("/issues/check-duplicates", response_model=Envelope[DuplicateCheckResponse])
async def check_duplicates(
    body: DuplicateCheckRequest,
    db: Annotated[AsyncSession, Depends(get_db)],
    _: Annotated[User, Depends(get_reporter_user)],
) -> Envelope[DuplicateCheckResponse]:
    similar = await duplicate_detection_service.find_similar(
        db,
        description=body.description,
        station_id=body.station_id,
        title=body.title,
    )
    similar_out = [similar_issue_to_out(s.issue, s.similarity) for s in similar]
    return Envelope(
        data=DuplicateCheckResponse(
            has_similar=len(similar_out) > 0,
            threshold=effective_duplicate_threshold(),
            similar_issues=similar_out,
            recommendation="support_existing" if similar_out else "create_new",
        ),
        meta=Meta(),
    )


@router.post("/issues", status_code=status.HTTP_201_CREATED)
async def create_issue(
    body: IssueCreateRequest,
    db: Annotated[AsyncSession, Depends(get_db)],
    user: Annotated[User, Depends(get_reporter_user)],
) -> Envelope[dict]:
    try:
        issue = await issue_service.create_issue(
            db,
            creator=user,
            station_id=body.station_id,
            description=body.description,
            title=body.title,
            platform_id=body.platform_id,
            train_number=body.train_number,
            coach_number=body.coach_number,
            pnr_number=body.pnr_number,
            berth_number=body.berth_number,
            upcoming_station_code=body.upcoming_station_code,
            latitude=body.latitude,
            longitude=body.longitude,
            force_create=body.force_create,
            divergence_reason=body.divergence_reason,
        )
    except DuplicateFoundError as exc:
        similar_out = [similar_issue_to_out(s.issue, s.similarity) for s in exc.similar]
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail={
                "code": "DUPLICATE_FOUND",
                "message": "Similar issues exist. Support existing or create with reason.",
                "similar_issues": [s.model_dump(mode="json") for s in similar_out],
            },
        ) from exc
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
            "ai_processing": {"status": "completed", "tasks": ["embed", "categorize", "spam_check", "priority"]},
        },
        meta=Meta(),
    )


@router.get("/issues/{issue_id}", response_model=Envelope[IssueDetailOut])
async def get_issue(
    issue_id: uuid.UUID,
    db: Annotated[AsyncSession, Depends(get_db)],
) -> Envelope[IssueDetailOut]:
    issue = await issue_service.get_issue_detail(db, issue_id)
    if not issue or not issue.is_public:
        raise HTTPException(status_code=404, detail="Issue not found")
    return Envelope(data=issue_detail_to_out(issue), meta=Meta())


@router.get("/issues")
async def list_issues(
    db: Annotated[AsyncSession, Depends(get_db)],
    station_code: str | None = Query(None),
    sort: str = Query("newest"),
    limit: int = Query(20, ge=1, le=100),
    cursor: str | None = Query(None),
) -> Envelope[dict]:
    query = (
        select(Issue)
        .options(selectinload(Issue.station), selectinload(Issue.category))
        .where(Issue.is_public.is_(True))
    )
    if station_code:
        query = query.join(Issue.station).where(Station.code == station_code.upper())

    sort_map = {
        "newest": Issue.created_at.desc(),
        "most_supported": Issue.support_count.desc(),
        "ai_priority": Issue.priority_score.desc(),
        "trending": Issue.trending_score.desc(),
    }
    query = query.order_by(sort_map.get(sort, Issue.created_at.desc())).limit(limit)
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


@router.post("/issues/{issue_id}/resolve-with-verification")
async def resolve_issue_with_verification(
    issue_id: uuid.UUID,
    db: Annotated[AsyncSession, Depends(get_db)],
    file: UploadFile = File(...),
):
    contents = await file.read()
    service = VisualResolverService(db)
    result = await service.verify_and_resolve_issue(issue_id, contents, file.filename or "resolution.jpg")
    if "error" in result:
        raise HTTPException(status_code=404, detail=result["error"])
    return Envelope(data=result, meta=Meta())


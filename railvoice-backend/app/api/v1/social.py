import uuid
from typing import Annotated

from fastapi import APIRouter, Depends, File, HTTPException, UploadFile, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.ai.image_validator import image_validator
from app.core.config import settings
from app.core.deps import get_current_user, get_db, get_reporter_user, require_official, user_is_official
from app.core.enums import TimelineEventType, Visibility
from app.models.issue import Comment, Issue, IssuePhoto, IssueTimelineEvent
from app.models.user import Notification, User
from app.schemas.common import (
    CommentCreateRequest,
    CommentOut,
    Envelope,
    Meta,
    NotificationOut,
    PhotoOut,
)
from app.schemas.mappers import comment_to_out, notification_to_out, photo_to_out
from app.services.storage import storage_service

comments_router = APIRouter(tags=["Comments"])
photos_router = APIRouter(tags=["Photos"])
notifications_router = APIRouter(prefix="/notifications", tags=["Notifications"])


@comments_router.get("/issues/{issue_id}/comments", response_model=Envelope[list[CommentOut]])
async def list_comments(
    issue_id: uuid.UUID,
    db: Annotated[AsyncSession, Depends(get_db)],
) -> Envelope[list[CommentOut]]:
    issue = await db.get(Issue, issue_id)
    if not issue or not issue.is_public:
        raise HTTPException(status_code=404, detail="Issue not found")
    result = await db.execute(
        select(Comment)
        .options(selectinload(Comment.user))
        .where(Comment.issue_id == issue_id, Comment.is_hidden.is_(False))
        .order_by(Comment.created_at.asc())
    )
    return Envelope(data=[comment_to_out(c) for c in result.scalars().all()], meta=Meta())


@comments_router.post(
    "/issues/{issue_id}/comments",
    status_code=status.HTTP_201_CREATED,
    response_model=Envelope[CommentOut],
)
async def create_comment(
    issue_id: uuid.UUID,
    body: CommentCreateRequest,
    db: Annotated[AsyncSession, Depends(get_db)],
    user: Annotated[User, Depends(get_current_user)],
) -> Envelope[CommentOut]:
    if user.is_anonymous:
        raise HTTPException(status_code=401, detail="Sign in to comment")
    issue = await db.get(Issue, issue_id)
    if not issue or not issue.is_public:
        raise HTTPException(status_code=404, detail="Issue not found")

    comment = Comment(
        issue_id=issue_id,
        user_id=user.id,
        parent_id=body.parent_id,
        body=body.body.strip(),
    )
    db.add(comment)
    issue.comment_count = (issue.comment_count or 0) + 1
    db.add(
        IssueTimelineEvent(
            issue_id=issue_id,
            event_type=TimelineEventType.COMMENT_ADDED.value,
            actor_id=user.id,
            remarks=body.body.strip()[:200],
            visibility=Visibility.PUBLIC.value,
        )
    )
    if issue.creator_id and issue.creator_id != user.id:
        db.add(
            Notification(
                user_id=issue.creator_id,
                type="comment",
                title="New comment on your issue",
                body=f"{user.display_name}: {body.body.strip()[:120]}",
                issue_id=issue_id,
            )
        )
    await db.flush()
    await db.refresh(comment)
    result = await db.execute(
        select(Comment).options(selectinload(Comment.user)).where(Comment.id == comment.id)
    )
    return Envelope(data=comment_to_out(result.scalar_one()), meta=Meta())


@comments_router.patch("/comments/{comment_id}/hide", response_model=Envelope[CommentOut])
async def hide_comment(
    comment_id: uuid.UUID,
    db: Annotated[AsyncSession, Depends(get_db)],
    officer: Annotated[User, Depends(require_official)],
) -> Envelope[CommentOut]:
    comment = await db.get(Comment, comment_id)
    if not comment:
        raise HTTPException(status_code=404, detail="Comment not found")
    comment.is_hidden = True
    issue = await db.get(Issue, comment.issue_id)
    if issue and issue.comment_count > 0:
        issue.comment_count -= 1
    await db.flush()
    result = await db.execute(
        select(Comment).options(selectinload(Comment.user)).where(Comment.id == comment.id)
    )
    return Envelope(data=comment_to_out(result.scalar_one()), meta=Meta())


@photos_router.post(
    "/issues/{issue_id}/photos",
    status_code=status.HTTP_201_CREATED,
    response_model=Envelope[PhotoOut],
)
async def upload_photo(
    issue_id: uuid.UUID,
    db: Annotated[AsyncSession, Depends(get_db)],
    user: Annotated[User, Depends(get_reporter_user)],
    file: UploadFile = File(...),
) -> Envelope[PhotoOut]:
    from sqlalchemy import func

    issue = await db.get(Issue, issue_id)
    if not issue:
        raise HTTPException(status_code=404, detail="Issue not found")
    is_owner = issue.creator_id == user.id
    if not is_owner and not user_is_official(user):
        raise HTTPException(status_code=403, detail="Only the reporter can upload photos")

    count = await db.scalar(
        select(func.count()).select_from(IssuePhoto).where(IssuePhoto.issue_id == issue_id)
    )
    if (count or 0) >= settings.max_photos_per_issue:
        raise HTTPException(status_code=400, detail="Photo limit reached for this issue")

    data = await file.read()
    try:
        mime = storage_service.validate_image_bytes(data)
    except ValueError as exc:
        raise HTTPException(
            status_code=400,
            detail={"code": "INVALID_IMAGE", "message": str(exc)},
        ) from exc

    validation = image_validator.validate(
        mime_type=mime,
        file_size_bytes=len(data),
        issue_description=issue.description,
    )
    if not validation.is_valid:
        raise HTTPException(
            status_code=400,
            detail={"code": "INVALID_IMAGE", "message": "Image rejected", "flags": validation.flags},
        )

    from app.ai.visual_verifier import visual_verifier

    p_hash, scan_status, visual_flags = await visual_verifier.verify_upload(db, data)

    key = storage_service.build_key(issue_id=issue_id, filename=file.filename or "photo.jpg")
    await storage_service.save_bytes(key, data, mime)
    photo = IssuePhoto(
        issue_id=issue_id,
        uploader_id=user.id,
        storage_key=key,
        mime_type=mime,
        file_size_bytes=len(data),
        perceptual_hash=p_hash,
        scan_status=scan_status,
        sort_order=count or 0,
    )
    db.add(photo)
    await db.flush()
    await db.refresh(photo)
    return Envelope(data=photo_to_out(photo), meta=Meta())


@notifications_router.get("", response_model=Envelope[dict])
async def list_notifications(
    db: Annotated[AsyncSession, Depends(get_db)],
    user: Annotated[User, Depends(get_current_user)],
    limit: int = 50,
) -> Envelope[dict]:
    result = await db.execute(
        select(Notification)
        .where(Notification.user_id == user.id)
        .order_by(Notification.created_at.desc())
        .limit(limit)
    )
    items = [notification_to_out(n) for n in result.scalars().all()]
    unread = sum(1 for n in items if not n.is_read)
    return Envelope(data={"items": [i.model_dump(mode="json") for i in items], "unread_count": unread}, meta=Meta())


@notifications_router.patch("/{notification_id}/read", response_model=Envelope[NotificationOut])
async def mark_notification_read(
    notification_id: uuid.UUID,
    db: Annotated[AsyncSession, Depends(get_db)],
    user: Annotated[User, Depends(get_current_user)],
) -> Envelope[NotificationOut]:
    note = await db.get(Notification, notification_id)
    if not note or note.user_id != user.id:
        raise HTTPException(status_code=404, detail="Notification not found")
    note.is_read = True
    await db.flush()
    return Envelope(data=notification_to_out(note), meta=Meta())


@notifications_router.post("/read-all", response_model=Envelope[dict])
async def mark_all_read(
    db: Annotated[AsyncSession, Depends(get_db)],
    user: Annotated[User, Depends(get_current_user)],
) -> Envelope[dict]:
    result = await db.execute(
        select(Notification).where(Notification.user_id == user.id, Notification.is_read.is_(False))
    )
    notes = result.scalars().all()
    for note in notes:
        note.is_read = True
    await db.flush()
    return Envelope(data={"marked": len(notes)}, meta=Meta())

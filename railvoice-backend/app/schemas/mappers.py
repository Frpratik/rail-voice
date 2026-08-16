from __future__ import annotations

from sqlalchemy import inspect as sa_inspect

from app.models.issue import Comment, Issue, IssuePhoto, IssueTimelineEvent
from app.models.location import IssueCategory, Station
from app.models.user import Notification, User
from app.schemas.common import (
    CategoryOut,
    CommentOut,
    DivisionOut,
    IssueDetailOut,
    IssueLocationOut,
    IssueOut,
    NotificationOut,
    PhotoOut,
    StationOut,
    TimelineEventOut,
    UserOut,
)
from app.services.storage import storage_service


def _loaded_attr(instance: object | None, name: str):
    """Return a relationship value only if it is already loaded (no DB IO)."""
    if instance is None:
        return None
    state = sa_inspect(instance)
    if name in state.unloaded:
        return None
    return getattr(instance, name)


def user_to_out(user: User) -> UserOut:
    from app.services.personas import persona_label, user_persona

    roles: list[str] = []
    try:
        user_roles = getattr(user, "roles", []) or []
        for user_role in user_roles:
            if getattr(user_role, "revoked_at", None) is not None:
                continue
            role = getattr(user_role, "role", None)
            if role is not None and hasattr(role, "code"):
                roles.append(role.code)
    except Exception:
        roles = []
    persona = user_persona(user) if roles or not user.is_anonymous else "passenger"
    return UserOut(
        id=user.id,
        display_name=user.display_name,
        is_verified=user.is_verified,
        is_anonymous=user.is_anonymous,
        roles=roles or (["passenger"] if not user.is_anonymous else []),
        persona=persona,
        persona_label=persona_label(persona),
    )


def station_to_out(station: Station, open_count: int | None = None) -> StationOut:
    division = None
    division_obj = _loaded_attr(station, "division")
    if division_obj is not None:
        division = DivisionOut(code=division_obj.code, name=division_obj.name)
    return StationOut(
        id=station.id,
        code=station.code,
        name=station.name,
        name_hi=station.name_hi,
        name_mr=station.name_mr,
        sequence_order=station.sequence_order,
        latitude=float(station.latitude),
        longitude=float(station.longitude),
        division=division,
        open_issue_count=open_count,
    )


def photo_to_out(photo: IssuePhoto) -> PhotoOut:
    return PhotoOut(
        id=photo.id,
        url=storage_service.public_url(photo.storage_key),
        mime_type=photo.mime_type,
        file_size_bytes=photo.file_size_bytes,
        scan_status=photo.scan_status,
        sort_order=photo.sort_order,
        created_at=photo.created_at,
    )


def comment_to_out(comment: Comment) -> CommentOut:
    author = _loaded_attr(comment, "user")
    return CommentOut(
        id=comment.id,
        issue_id=comment.issue_id,
        body=comment.body,
        parent_id=comment.parent_id,
        is_hidden=comment.is_hidden,
        created_at=comment.created_at,
        author={
            "id": str(author.id) if author else None,
            "display_name": author.display_name if author else "User",
            "is_anonymous": bool(author.is_anonymous) if author else False,
        },
    )


def notification_to_out(note: Notification) -> NotificationOut:
    return NotificationOut(
        id=note.id,
        type=note.type,
        title=note.title,
        body=note.body,
        issue_id=note.issue_id,
        is_read=note.is_read,
        created_at=note.created_at,
    )


def issue_to_out(
    issue: Issue,
    *,
    station: Station | None = None,
    category: IssueCategory | None = None,
    creator: User | None = None,
) -> IssueOut:
    station_obj = station if station is not None else _loaded_attr(issue, "station")
    category_obj = category if category is not None else _loaded_attr(issue, "category")
    creator_obj = creator if creator is not None else _loaded_attr(issue, "creator")

    if station_obj is not None:
        station_payload = {
            "code": station_obj.code,
            "name": station_obj.name,
            "id": str(station_obj.id),
        }
    elif issue.station_id:
        station_payload = {"id": str(issue.station_id)}
    else:
        station_payload = {}

    location = IssueLocationOut(
        station=station_payload,
        train_number=issue.train_number,
        coach_number=issue.coach_number,
        pnr_number=issue.pnr_number,
        berth_number=issue.berth_number,
        upcoming_station_code=issue.upcoming_station_code,
        latitude=float(issue.latitude) if issue.latitude is not None else None,
        longitude=float(issue.longitude) if issue.longitude is not None else None,
    )

    category_out = CategoryOut.model_validate(category_obj) if category_obj is not None else None
    creator_out = None
    if creator_obj is not None:
        creator_out = {
            "id": str(creator_obj.id),
            "display_name": creator_obj.display_name,
            "is_anonymous": creator_obj.is_anonymous,
        }

    assignee_out = None
    assignee_obj = _loaded_attr(issue, "assignee")
    if assignee_obj is not None:
        assignee_out = {
            "id": str(assignee_obj.id),
            "display_name": assignee_obj.display_name,
        }
    elif getattr(issue, "assignee_id", None):
        assignee_out = {"id": str(issue.assignee_id)}

    photos = [photo_to_out(p) for p in sorted(_loaded_attr(issue, "photos") or [], key=lambda x: x.sort_order)]

    return IssueOut(
        id=issue.id,
        issue_number=issue.issue_number,
        title=issue.title,
        description=issue.description,
        status=issue.status,
        severity=issue.severity,
        is_emergency=issue.is_emergency,
        support_count=issue.support_count,
        comment_count=issue.comment_count,
        category=category_out,
        location=location,
        creator=creator_out,
        assignee=assignee_out,
        photos=photos,
        created_at=issue.created_at,
        updated_at=issue.updated_at,
        resolved_at=issue.resolved_at,
        closed_at=issue.closed_at,
    )


def issue_detail_to_out(issue: Issue, include_internal: bool = False) -> IssueDetailOut:
    timeline = []
    for event in sorted(_loaded_attr(issue, "timeline_events") or [], key=lambda e: e.created_at):
        if not include_internal and event.visibility != "public":
            continue
        timeline.append(TimelineEventOut.model_validate(event))
    comments = [
        comment_to_out(c)
        for c in sorted(_loaded_attr(issue, "comments") or [], key=lambda e: e.created_at)
        if not c.is_hidden
    ]
    return IssueDetailOut(issue=issue_to_out(issue), timeline=timeline, comments=comments)

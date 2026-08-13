from __future__ import annotations

import uuid
from datetime import datetime
from typing import Any, Generic, TypeVar

from pydantic import BaseModel, ConfigDict, Field

T = TypeVar("T")


class Meta(BaseModel):
    correlation_id: str | None = None
    timestamp: datetime = Field(default_factory=datetime.utcnow)


class Pagination(BaseModel):
    next_cursor: str | None = None
    prev_cursor: str | None = None
    has_more: bool = False
    total_count: int | None = None


class Envelope(BaseModel, Generic[T]):
    data: T
    meta: Meta = Field(default_factory=Meta)


class ErrorDetail(BaseModel):
    code: str
    message: str
    details: dict[str, Any] | None = None
    correlation_id: str | None = None


class ErrorEnvelope(BaseModel):
    error: ErrorDetail


class OTPRequestBody(BaseModel):
    mobile: str = Field(..., pattern=r"^\+91\d{10}$")


class OTPVerifyBody(BaseModel):
    mobile: str = Field(..., pattern=r"^\+91\d{10}$")
    otp: str = Field(..., min_length=6, max_length=6)


class UserOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    display_name: str
    is_verified: bool
    is_anonymous: bool = False
    roles: list[str] = []
    persona: str = "passenger"
    persona_label: str = "Passenger"


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "Bearer"
    expires_in: int
    refresh_token: str | None = None
    user: UserOut


class GoogleAuthRequest(BaseModel):
    id_token: str = Field(..., min_length=4)
    email: str | None = None
    name: str | None = None
    google_id: str | None = None
    avatar_url: str | None = None


class RefreshRequest(BaseModel):
    refresh_token: str | None = None


class AnonymousSessionOut(BaseModel):
    anonymous_session_id: uuid.UUID
    expires_in: int = 86400
    limits: dict[str, int]


class DivisionOut(BaseModel):
    code: str
    name: str


class StationOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    code: str
    name: str
    name_hi: str | None = None
    name_mr: str | None = None
    sequence_order: int
    latitude: float
    longitude: float
    division: DivisionOut | None = None
    open_issue_count: int | None = None


class CategoryOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    code: str
    name: str
    icon: str | None = None


class IssueCreateRequest(BaseModel):
    description: str = Field(..., min_length=10, max_length=5000)
    station_id: uuid.UUID
    title: str | None = Field(None, max_length=200)
    category_id: uuid.UUID | None = None
    platform_id: uuid.UUID | None = None
    train_number: str | None = Field(None, max_length=10)
    coach_number: str | None = Field(None, max_length=10)
    pnr_number: str | None = Field(None, max_length=10)
    berth_number: str | None = Field(None, max_length=10)
    upcoming_station_code: str | None = Field(None, max_length=10)
    is_emergency: bool = False
    latitude: float | None = None
    longitude: float | None = None


class IssueLocationOut(BaseModel):
    station: dict[str, Any]
    platform: dict[str, Any] | None = None
    train_number: str | None = None
    coach_number: str | None = None
    pnr_number: str | None = None
    berth_number: str | None = None
    upcoming_station_code: str | None = None
    latitude: float | None = None
    longitude: float | None = None


class CommentCreateRequest(BaseModel):
    body: str = Field(..., min_length=1, max_length=2000)
    parent_id: uuid.UUID | None = None


class CommentOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    issue_id: uuid.UUID
    body: str
    parent_id: uuid.UUID | None = None
    is_hidden: bool = False
    created_at: datetime
    author: dict[str, Any]


class PhotoOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    url: str
    mime_type: str
    file_size_bytes: int
    scan_status: str
    sort_order: int
    created_at: datetime


class NotificationOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    type: str
    title: str
    body: str
    issue_id: uuid.UUID | None = None
    is_read: bool
    created_at: datetime


class AssignRequest(BaseModel):
    assignee_id: uuid.UUID
    remarks: str = Field(..., min_length=5, max_length=2000)


class EscalateRequest(BaseModel):
    target: str = Field(..., pattern=r"^(station_manager|division|zone)$")
    remarks: str = Field(..., min_length=5, max_length=2000)


class NotifyMainAdminRequest(BaseModel):
    remarks: str = Field(
        default="Station report ready for review",
        min_length=5,
        max_length=500,
    )


class IssueOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    issue_number: str
    title: str | None
    description: str
    status: str
    severity: int
    is_emergency: bool
    support_count: int
    comment_count: int
    category: CategoryOut | None = None
    location: IssueLocationOut
    creator: dict[str, Any] | None = None
    assignee: dict[str, Any] | None = None
    photos: list[PhotoOut] = []
    created_at: datetime
    updated_at: datetime
    resolved_at: datetime | None = None
    closed_at: datetime | None = None


class TimelineEventOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    event_type: str
    from_status: str | None
    to_status: str | None
    remarks: str | None
    visibility: str
    created_at: datetime


class IssueDetailOut(BaseModel):
    issue: IssueOut
    timeline: list[TimelineEventOut]
    comments: list[CommentOut] = []


class SupportResponse(BaseModel):
    issue_id: uuid.UUID
    support_count: int
    subscribed_to_updates: bool = True
    message: str


class StatusUpdateRequest(BaseModel):
    status: str
    remarks: str = Field(..., min_length=5, max_length=2000)
    visibility: str = "public"


class DashboardKPIs(BaseModel):
    open_issues: int
    in_progress: int
    resolved_today: int
    avg_resolution_hours: float | None
    sla_breaches: int
    emergency_open: int

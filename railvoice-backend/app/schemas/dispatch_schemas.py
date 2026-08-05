import uuid
from datetime import datetime
from pydantic import BaseModel, ConfigDict, Field

class WorkforceStaffOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    full_name: str
    skill_category: str
    contact_number: str | None = None
    assigned_station_id: uuid.UUID | None = None
    status: str
    shift_start: str | None = None
    shift_end: str | None = None
    is_active: bool
    created_at: datetime

class DispatchRecommendationOut(BaseModel):
    issue_id: uuid.UUID
    issue_number: str
    title: str | None = None
    station_name: str
    category_name: str
    priority_score: float
    recommended_staff: WorkforceStaffOut
    skill_match: str
    confidence_score: float
    reason: str

class DispatchAssignmentOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    issue_id: uuid.UUID
    staff_id: uuid.UUID
    dispatch_status: str
    matched_skill: str | None = None
    confidence_score: float | None = None
    dispatched_at: datetime
    completed_at: datetime | None = None
    staff: WorkforceStaffOut | None = None

class RosterSummaryOut(BaseModel):
    total_staff: int
    available_count: int
    on_task_count: int
    off_duty_count: int
    category_counts: dict[str, int]
    staff_list: list[WorkforceStaffOut]

class AutoDispatchResultOut(BaseModel):
    dispatched_count: int
    assignments: list[DispatchAssignmentOut]

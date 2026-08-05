import uuid
from datetime import datetime
from sqlalchemy import Boolean, DateTime, ForeignKey, Numeric, String, func
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.db.session import Base

class WorkforceStaff(Base):
    __tablename__ = "workforce_staff"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    full_name: Mapped[str] = mapped_column(String(150), nullable=False)
    skill_category: Mapped[str] = mapped_column(String(50), nullable=False) # housekeeping, electrical, mechanical, safety
    contact_number: Mapped[str | None] = mapped_column(String(20))
    assigned_station_id: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True), ForeignKey("stations.id"))
    status: Mapped[str] = mapped_column(String(30), default="available", nullable=False) # available, on_task, off_duty
    shift_start: Mapped[str | None] = mapped_column(String(10))
    shift_end: Mapped[str | None] = mapped_column(String(10))
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    assigned_station = relationship("Station", lazy="selectin")
    dispatch_assignments = relationship("DispatchAssignment", back_populates="staff")


class DispatchAssignment(Base):
    __tablename__ = "dispatch_assignments"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    issue_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("issues.id"), nullable=False)
    staff_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("workforce_staff.id"), nullable=False)
    dispatch_status: Mapped[str] = mapped_column(String(30), default="dispatched", nullable=False) # dispatched, accepted, in_progress, completed
    matched_skill: Mapped[str | None] = mapped_column(String(50))
    confidence_score: Mapped[float | None] = mapped_column(Numeric(5, 2))
    dispatched_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    completed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))

    issue = relationship("Issue", lazy="selectin")
    staff = relationship("WorkforceStaff", back_populates="dispatch_assignments", lazy="selectin")

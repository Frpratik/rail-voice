import uuid
from datetime import datetime

from sqlalchemy import DateTime, ForeignKey, Integer, String, func
from sqlalchemy.dialects.postgresql import ARRAY, UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.session import Base


class UserReputation(Base):
    __tablename__ = "user_reputations"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False, unique=True)
    points: Mapped[int] = mapped_column(Integer, default=0, index=True)
    tier: Mapped[str] = mapped_column(String(20), default="bronze")  # bronze | silver | gold | platinum
    badge_slugs: Mapped[list[str]] = mapped_column(ARRAY(String), default=list)
    reports_count: Mapped[int] = mapped_column(Integer, default=0)
    verifications_count: Mapped[int] = mapped_column(Integer, default=0)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

    user = relationship("User")

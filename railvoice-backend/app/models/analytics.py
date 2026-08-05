import uuid
from datetime import datetime, timezone
from sqlalchemy import Column, String, Float, Integer, DateTime, ForeignKey
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship

from app.db.session import Base

class StationHealthSnapshot(Base):
    __tablename__ = "station_health_snapshots"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    station_id = Column(UUID(as_uuid=True), ForeignKey("stations.id"), nullable=False)
    health_score = Column(Float, nullable=False, default=100.0)
    active_issues_count = Column(Integer, nullable=False, default=0)
    critical_issues_count = Column(Integer, nullable=False, default=0)
    snapshot_date = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))

    station = relationship("Station")

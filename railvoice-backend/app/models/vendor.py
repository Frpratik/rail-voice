import uuid
from sqlalchemy import Column, String, Boolean, Numeric, DateTime, ForeignKey, Text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.sql import func
from app.db.session import Base
from sqlalchemy.orm import relationship

class VendorContract(Base):
    __tablename__ = "vendor_contracts"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    vendor_name = Column(String(255), nullable=False)
    contract_code = Column(String(50), unique=True, nullable=False, index=True)
    station_id = Column(UUID(as_uuid=True), ForeignKey("stations.id"), nullable=True)
    category_id = Column(UUID(as_uuid=True), ForeignKey("issue_categories.id"), nullable=True)
    penalty_per_sla_hour = Column(Numeric(10, 2), nullable=False)
    max_penalty_cap = Column(Numeric(10, 2), nullable=False)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    station = relationship("Station", lazy="joined")
    category = relationship("IssueCategory", lazy="joined")
    penalty_notes = relationship("VendorPenaltyNote", back_populates="contract")


class VendorPenaltyNote(Base):
    __tablename__ = "vendor_penalty_notes"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    contract_id = Column(UUID(as_uuid=True), ForeignKey("vendor_contracts.id"), nullable=False)
    issue_id = Column(UUID(as_uuid=True), ForeignKey("issues.id"), nullable=False)
    penalty_amount = Column(Numeric(10, 2), nullable=False)
    clause_reference = Column(String(100), nullable=False)
    status = Column(String(50), default="pending_review") # pending_review, approved, disputed
    pdf_url = Column(String(512), nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    contract = relationship("VendorContract", back_populates="penalty_notes")
    issue = relationship("Issue", lazy="joined")

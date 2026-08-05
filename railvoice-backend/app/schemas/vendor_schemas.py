from pydantic import BaseModel
from typing import Optional, List
from datetime import datetime
from uuid import UUID
from decimal import Decimal

# Shared schemas
class VendorContractBase(BaseModel):
    vendor_name: str
    contract_code: str
    station_id: Optional[UUID] = None
    category_id: Optional[UUID] = None
    penalty_per_sla_hour: Decimal
    max_penalty_cap: Decimal
    is_active: bool = True

class VendorContractCreate(VendorContractBase):
    pass

class VendorContractOut(VendorContractBase):
    id: UUID
    created_at: datetime

    class Config:
        from_attributes = True

class VendorPenaltyNoteBase(BaseModel):
    contract_id: UUID
    issue_id: UUID
    penalty_amount: Decimal
    clause_reference: str
    status: str
    pdf_url: Optional[str] = None

class VendorPenaltyNoteOut(VendorPenaltyNoteBase):
    id: UUID
    created_at: datetime

    class Config:
        from_attributes = True

class VendorScorecardItem(BaseModel):
    contract: VendorContractOut
    total_penalty_deducted: Decimal
    pending_penalties: Decimal
    sla_breaches_count: int
    resolved_issues_count: int

class VendorScorecardResponse(BaseModel):
    items: List[VendorScorecardItem]

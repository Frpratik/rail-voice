import os
from uuid import UUID
from datetime import datetime, timezone
from decimal import Decimal
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.models.vendor import VendorContract, VendorPenaltyNote
from app.models.issue import Issue
from app.models.location import Station, IssueCategory
from app.schemas.vendor_schemas import VendorScorecardResponse, VendorScorecardItem, VendorContractOut

# We can import reportlab later.
from reportlab.lib.pagesizes import A4
from reportlab.pdfgen import canvas
from reportlab.lib.units import inch

# Store PDF in a static directory, e.g. static/reports
REPORTS_DIR = os.path.join(os.getcwd(), "static", "reports")
os.makedirs(REPORTS_DIR, exist_ok=True)

class VendorPenaltyService:
    def __init__(self, db: AsyncSession):
        self.db = db

    def generate_pdf_debit_note(self, penalty_note: VendorPenaltyNote, contract: VendorContract, issue: Issue) -> str:
        filename = f"debit_note_{penalty_note.id}.pdf"
        filepath = os.path.join(REPORTS_DIR, filename)

        c = canvas.Canvas(filepath, pagesize=A4)
        c.setFont("Helvetica-Bold", 16)
        c.drawString(1 * inch, 10.5 * inch, "INDIAN RAILWAYS - VENDOR PENALTY DEBIT NOTE")

        c.setFont("Helvetica", 12)
        c.drawString(1 * inch, 10 * inch, f"Date: {penalty_note.created_at.strftime('%Y-%m-%d %H:%M:%S')}")
        c.drawString(1 * inch, 9.5 * inch, f"Note ID: {penalty_note.id}")
        c.drawString(1 * inch, 9 * inch, f"Contract Code: {contract.contract_code}")
        c.drawString(1 * inch, 8.5 * inch, f"Vendor Name: {contract.vendor_name}")

        # The issue model doesn't have an issue_number column. Let's just use the ID.
        c.drawString(1 * inch, 7.5 * inch, f"Issue ID: {issue.id}")
        c.drawString(1 * inch, 7 * inch, f"SLA Breach Penalty Clause: {penalty_note.clause_reference}")
        
        c.setFont("Helvetica-Bold", 14)
        c.drawString(1 * inch, 6 * inch, f"Total Penalty Deducted: Rs. {penalty_note.penalty_amount}")
        
        c.setFont("Helvetica", 10)
        c.drawString(1 * inch, 5 * inch, "This is an automatically generated document from RailVoice Operations Engine.")
        
        c.save()
        return f"/static/reports/{filename}"

    async def trigger_penalty_engine(self):
        """
        Calculates SLA breaches for all active contracts and applies penalties.
        A real system would do this daily via Celery or Cron.
        """
        # Find all active contracts
        result = await self.db.execute(select(VendorContract).where(VendorContract.is_active == True))
        contracts = result.scalars().all()
        
        notes_created = 0
        for contract in contracts:
            # Subquery to find issues matching station and category
            stmt = select(Issue).where(
                Issue.station_id == contract.station_id,
                Issue.category_id == contract.category_id,
                Issue.status.in_(["OPEN", "IN_PROGRESS"])
            )
            issue_result = await self.db.execute(stmt)
            issues = issue_result.scalars().all()
            
            for issue in issues:
                # Check if older than 4 hours
                # created_at might be naive in some dbs, but assuming UTC
                delta = datetime.now(timezone.utc).replace(tzinfo=None) - issue.created_at.replace(tzinfo=None)
                hours_delayed = delta.total_seconds() / 3600
                if hours_delayed > 4:
                    # Check if a penalty note already exists for this issue and contract
                    existing = await self.db.execute(select(VendorPenaltyNote).where(
                        VendorPenaltyNote.contract_id == contract.id,
                        VendorPenaltyNote.issue_id == issue.id
                    ))
                    existing_note = existing.scalar_one_or_none()
                    
                    if existing_note:
                        continue # Already penalized
                    
                    # Calculate penalty
                    penalty_amount = contract.penalty_per_sla_hour * Decimal(hours_delayed - 4)
                    if penalty_amount > contract.max_penalty_cap:
                        penalty_amount = contract.max_penalty_cap
                        
                    # Create Note
                    # we must pre-assign an ID because the object is uncommitted before pdf generation,
                    # but postgres will generate it on commit. So let's add, flush.
                    note = VendorPenaltyNote(
                        contract_id=contract.id,
                        issue_id=issue.id,
                        penalty_amount=penalty_amount,
                        clause_reference=f"SLA Breach > 4 hrs ({hours_delayed:.1f} hrs total)",
                        status="pending_review"
                    )
                    self.db.add(note)
                    await self.db.flush()
                    await self.db.refresh(note)
                    
                    # Generate PDF
                    # need to mock created_at if it's not set
                    if not note.created_at:
                        note.created_at = datetime.now()
                        
                    pdf_url = self.generate_pdf_debit_note(note, contract, issue)
                    note.pdf_url = pdf_url
                    await self.db.commit()
                    notes_created += 1

        return {"status": "success", "penalty_notes_created": notes_created}

    async def get_scorecard(self) -> VendorScorecardResponse:
        res = await self.db.execute(select(VendorContract))
        contracts = res.scalars().all()
        items = []
        for contract in contracts:
            n_res = await self.db.execute(select(VendorPenaltyNote).where(VendorPenaltyNote.contract_id == contract.id))
            notes = n_res.scalars().all()
            
            total_deducted = sum([n.penalty_amount for n in notes if n.status == "approved"])
            pending = sum([n.penalty_amount for n in notes if n.status == "pending_review"])
            sla_breaches = len(notes)
            
            # mock resolved issues count
            stmt = select(Issue).where(
                Issue.station_id == contract.station_id,
                Issue.category_id == contract.category_id,
                Issue.status == "RESOLVED"
            )
            iss_res = await self.db.execute(stmt)
            resolved = len(iss_res.scalars().all())
            
            c_out = VendorContractOut(
                id=contract.id,
                vendor_name=contract.vendor_name,
                contract_code=contract.contract_code,
                station_id=contract.station_id,
                category_id=contract.category_id,
                penalty_per_sla_hour=contract.penalty_per_sla_hour,
                max_penalty_cap=contract.max_penalty_cap,
                is_active=contract.is_active,
                created_at=contract.created_at
            )
            items.append(VendorScorecardItem(
                contract=c_out,
                total_penalty_deducted=total_deducted,
                pending_penalties=pending,
                sla_breaches_count=sla_breaches,
                resolved_issues_count=resolved
            ))
        return VendorScorecardResponse(items=items)

    async def approve_penalty(self, note_id: str):
        res = await self.db.execute(select(VendorPenaltyNote).where(VendorPenaltyNote.id == note_id))
        note = res.scalar_one_or_none()
        if note:
            note.status = "approved"
            await self.db.commit()
            return {"status": "success"}
        return {"status": "not_found"}

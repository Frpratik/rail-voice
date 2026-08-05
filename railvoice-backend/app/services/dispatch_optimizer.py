import uuid
from datetime import datetime, timezone
from typing import Sequence
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.models.dispatch import DispatchAssignment, WorkforceStaff
from app.models.issue import Issue
from app.schemas.dispatch_schemas import (
    AutoDispatchResultOut,
    DispatchAssignmentOut,
    DispatchRecommendationOut,
    RosterSummaryOut,
    WorkforceStaffOut,
)

CATEGORY_SKILL_MAP = {
    "cleanliness": "housekeeping",
    "sanitation": "housekeeping",
    "toilet": "housekeeping",
    "electrical": "electrical",
    "light": "electrical",
    "fan": "electrical",
    "ac": "electrical",
    "water": "mechanical",
    "escalator": "mechanical",
    "lift": "mechanical",
    "bench": "mechanical",
    "safety": "safety",
    "security": "safety",
    "medical": "safety",
}

class DispatchOptimizerService:
    async def get_roster_summary(self, db: AsyncSession) -> RosterSummaryOut:
        res = await db.execute(select(WorkforceStaff).where(WorkforceStaff.is_active.is_(True)))
        staff_members = res.scalars().all()

        total_staff = len(staff_members)
        available_count = sum(1 for s in staff_members if s.status == "available")
        on_task_count = sum(1 for s in staff_members if s.status == "on_task")
        off_duty_count = sum(1 for s in staff_members if s.status == "off_duty")

        category_counts: dict[str, int] = {}
        for s in staff_members:
            category_counts[s.skill_category] = category_counts.get(s.skill_category, 0) + 1

        return RosterSummaryOut(
            total_staff=total_staff,
            available_count=available_count,
            on_task_count=on_task_count,
            off_duty_count=off_duty_count,
            category_counts=category_counts,
            staff_list=[WorkforceStaffOut.model_validate(s) for s in staff_members],
        )

    async def generate_recommendations(self, db: AsyncSession) -> list[DispatchRecommendationOut]:
        # Fetch open uncompleted issues
        issues_res = await db.execute(
            select(Issue)
            .options(selectinload(Issue.station), selectinload(Issue.category))
            .where(Issue.is_public.is_(True))
            .where(Issue.status.in_(["submitted", "acknowledged", "assigned", "in_progress"]))
            .order_by(Issue.priority_score.desc())
            .limit(20)
        )
        issues = issues_res.scalars().all()

        # Fetch available staff
        staff_res = await db.execute(
            select(WorkforceStaff)
            .where(WorkforceStaff.is_active.is_(True))
            .where(WorkforceStaff.status == "available")
        )
        available_staff = list(staff_res.scalars().all())

        recommendations: list[DispatchRecommendationOut] = []
        assigned_staff_ids: set[uuid.UUID] = set()

        for issue in issues:
            cat_name = (issue.category.name if issue.category else "general").lower()
            station_name = issue.station.name if issue.station else "Corridor"
            
            # Map category to required skill
            required_skill = "housekeeping"
            for key, val in CATEGORY_SKILL_MAP.items():
                if key in cat_name or key in (issue.title or "").lower() or key in issue.description.lower():
                    required_skill = val
                    break

            # Find matching available staff
            matching_staff = [
                s for s in available_staff
                if s.id not in assigned_staff_ids and (
                    s.skill_category == required_skill or s.assigned_station_id == issue.station_id
                )
            ]

            if not matching_staff and available_staff:
                # Fallback to any unassigned available staff
                matching_staff = [s for s in available_staff if s.id not in assigned_staff_ids]

            if matching_staff:
                best_staff = matching_staff[0]
                assigned_staff_ids.add(best_staff.id)

                confidence = 94.5 if best_staff.skill_category == required_skill else 82.0
                reason = (
                    f"Optimal skill match ({required_skill.capitalize()}) and station availability."
                    if best_staff.skill_category == required_skill
                    else "General available staff dispatch fallback."
                )

                recommendations.append(
                    DispatchRecommendationOut(
                        issue_id=issue.id,
                        issue_number=issue.issue_number,
                        title=issue.title,
                        station_name=station_name,
                        category_name=issue.category.name if issue.category else "General Maintenance",
                        priority_score=float(issue.priority_score or 0),
                        recommended_staff=WorkforceStaffOut.model_validate(best_staff),
                        skill_match=required_skill,
                        confidence_score=confidence,
                        reason=reason,
                    )
                )

        return recommendations

    async def auto_dispatch_all(self, db: AsyncSession) -> AutoDispatchResultOut:
        recommendations = await self.generate_recommendations(db)
        assignments_out: list[DispatchAssignmentOut] = []

        for rec in recommendations:
            now_time = datetime.now(timezone.utc)
            assignment = DispatchAssignment(
                id=uuid.uuid4(),
                issue_id=rec.issue_id,
                staff_id=rec.recommended_staff.id,
                dispatch_status="dispatched",
                matched_skill=rec.skill_match,
                confidence_score=rec.confidence_score,
                dispatched_at=now_time,
            )
            db.add(assignment)

            # Update staff status to on_task
            staff_res = await db.execute(select(WorkforceStaff).where(WorkforceStaff.id == rec.recommended_staff.id))
            staff = staff_res.scalars().first()
            if staff:
                staff.status = "on_task"

            assignments_out.append(
                DispatchAssignmentOut(
                    id=assignment.id,
                    issue_id=assignment.issue_id,
                    staff_id=assignment.staff_id,
                    dispatch_status=assignment.dispatch_status,
                    matched_skill=assignment.matched_skill,
                    confidence_score=assignment.confidence_score,
                    dispatched_at=now_time,
                    completed_at=None,
                    staff=rec.recommended_staff,
                )
            )

        await db.commit()

        return AutoDispatchResultOut(
            dispatched_count=len(assignments_out),
            assignments=assignments_out,
        )

dispatch_optimizer_service = DispatchOptimizerService()

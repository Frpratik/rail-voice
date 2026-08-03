from __future__ import annotations

import uuid
from typing import Annotated, Any

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, Field
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.deps import get_db
from app.core.enums import IssueStatus, TimelineEventType
from app.models.issue import Issue, IssueFeedback, IssueTimelineEvent
from app.schemas.common import Envelope, Meta

router = APIRouter(prefix="/issues", tags=["CSAT Feedback & Reopen"])


class CSATFeedbackRequest(BaseModel):
    rating: int = Field(..., ge=1, le=5, description="Satisfaction rating from 1 (Poor) to 5 (Excellent)")
    comments: str | None = Field(None, max_length=1000)
    is_reopened: bool = Field(False, description="Set True if issue remains unresolved and needs reopening")
    reopen_reason: str | None = Field(None, max_length=1000, description="Mandatory reason if reopening issue")


class CSATFeedbackResponse(BaseModel):
    feedback_id: str
    issue_id: str
    rating: int
    comments: str | None
    is_reopened: bool
    reopen_reason: str | None
    new_status: str
    reopen_count: int
    priority_score: float


@router.post("/{issue_id}/feedback", response_model=Envelope[CSATFeedbackResponse])
async def submit_issue_csat_feedback(
    issue_id: uuid.UUID,
    body: CSATFeedbackRequest,
    db: Annotated[AsyncSession, Depends(get_db)],
) -> Envelope[CSATFeedbackResponse]:
    """Submit 1-5 star CSAT feedback or trigger 1-click grievance reopening."""
    issue = await db.scalar(select(Issue).where(Issue.id == issue_id))
    if not issue:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Issue not found")

    if body.is_reopened and (not body.reopen_reason or len(body.reopen_reason.strip()) < 5):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="reopen_reason with at least 5 characters is required when reopening an issue",
        )

    # Check for existing feedback
    existing_feedback = await db.scalar(select(IssueFeedback).where(IssueFeedback.issue_id == issue_id))
    if existing_feedback:
        existing_feedback.rating = body.rating
        existing_feedback.comments = body.comments
        existing_feedback.is_reopened = body.is_reopened
        existing_feedback.reopen_reason = body.reopen_reason
        feedback_obj = existing_feedback
    else:
        feedback_obj = IssueFeedback(
            issue_id=issue_id,
            rating=body.rating,
            comments=body.comments,
            is_reopened=body.is_reopened,
            reopen_reason=body.reopen_reason,
        )
        db.add(feedback_obj)

    # Handle Ticket Reopening if rating <= 2 or is_reopened is True
    should_reopen = body.is_reopened or body.rating <= 2
    if should_reopen:
        # Log Timeline Event
        event = IssueTimelineEvent(
            issue_id=issue.id,
            event_type=TimelineEventType.STATUS_CHANGE.value,
            from_status=issue.status,
            to_status=IssueStatus.WORK_IN_PROGRESS.value,
            remarks=f"Reopened by commuter (CSAT {body.rating}/5 Stars). Reason: {body.reopen_reason or 'Unsatisfactory rating'}",
        )
        db.add(event)

        issue.status = IssueStatus.WORK_IN_PROGRESS.value
        issue.reopen_count = (issue.reopen_count or 0) + 1
        current_score = float(issue.priority_score) if issue.priority_score is not None else 0.0
        issue.priority_score = current_score + 25.0

    await db.commit()

    return Envelope(
        data=CSATFeedbackResponse(
            feedback_id=str(feedback_obj.id),
            issue_id=str(issue.id),
            rating=feedback_obj.rating,
            comments=feedback_obj.comments,
            is_reopened=feedback_obj.is_reopened,
            reopen_reason=feedback_obj.reopen_reason,
            new_status=issue.status,
            reopen_count=issue.reopen_count,
            priority_score=float(issue.priority_score),
        ),
        meta=Meta(),
    )


@router.get("/{issue_id}/feedback", response_model=Envelope[CSATFeedbackResponse | None])
async def get_issue_csat_feedback(
    issue_id: uuid.UUID,
    db: Annotated[AsyncSession, Depends(get_db)],
) -> Envelope[CSATFeedbackResponse | None]:
    """Get existing CSAT feedback for an issue."""
    issue = await db.scalar(select(Issue).where(Issue.id == issue_id))
    if not issue:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Issue not found")

    feedback_obj = await db.scalar(select(IssueFeedback).where(IssueFeedback.issue_id == issue_id))
    if not feedback_obj:
        return Envelope(data=None, meta=Meta())

    return Envelope(
        data=CSATFeedbackResponse(
            feedback_id=str(feedback_obj.id),
            issue_id=str(issue.id),
            rating=feedback_obj.rating,
            comments=feedback_obj.comments,
            is_reopened=feedback_obj.is_reopened,
            reopen_reason=feedback_obj.reopen_reason,
            new_status=issue.status,
            reopen_count=issue.reopen_count,
            priority_score=float(issue.priority_score),
        ),
        meta=Meta(),
    )

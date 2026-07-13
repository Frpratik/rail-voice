from __future__ import annotations

from datetime import datetime, timezone

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.ai.categorizer import issue_categorizer
from app.ai.embeddings import embedding_service
from app.ai.priority import compute_priority_score
from app.ai.priority_predictor import priority_predictor
from app.ai.schemas import IssueAIAnalysis
from app.ai.severity import severity_predictor
from app.ai.spam import spam_detector
from app.ai.summarizer import issue_summarizer
from app.core.config import settings
from app.core.enums import IssueStatus
from app.models.issue import Issue
from app.models.location import IssueCategory


class IssueAIPipeline:
    """Orchestrates all AI steps for issue creation and enrichment."""

    async def analyze(
        self,
        *,
        description: str,
        title: str | None = None,
        is_anonymous: bool = False,
        has_photo: bool = False,
    ) -> IssueAIAnalysis:
        embed_text = f"{title or ''} {description}".strip()
        embedding = (await embedding_service.embed([embed_text]))[0]

        category = issue_categorizer.predict(description, title)
        severity = severity_predictor.predict(description, category)
        spam = spam_detector.predict(
            description,
            is_anonymous=is_anonymous,
            has_photo=has_photo,
        )
        priority = priority_predictor.predict(
            category=category,
            spam=spam,
            severity=severity,
            description=description,
        )
        summary = issue_summarizer.summarize(description, title)

        return IssueAIAnalysis(
            embedding=embedding,
            embedding_model=settings.embedding_model,
            category=category,
            spam=spam,
            priority=priority,
            summary=summary,
        )

    async def apply_to_issue(
        self,
        db: AsyncSession,
        issue: Issue,
        analysis: IssueAIAnalysis,
    ) -> Issue:
        issue.embedding = analysis.embedding
        issue.embedding_model = analysis.embedding_model
        issue.spam_score = analysis.spam.spam_score
        issue.severity = severity_predictor.predict(issue.description, analysis.category)
        issue.is_emergency = analysis.priority.is_emergency
        issue.ai_priority_score = analysis.priority.ai_priority_score

        cat = await self._resolve_category(db, analysis.category.category_code)
        sub = None
        if analysis.category.subcategory_code:
            sub = await self._resolve_category(db, analysis.category.subcategory_code)

        issue.category_id = cat.id if cat else None
        issue.subcategory_id = sub.id if sub else None

        if analysis.spam.is_auto_hold:
            issue.status = IssueStatus.SPAM.value
            issue.is_public = False
        else:
            issue.is_public = True

        issue.priority_score = compute_priority_score(
            support_count=issue.support_count or 0,
            severity=issue.severity,
            created_at=issue.created_at or datetime.now(timezone.utc),
            ai_priority_score=analysis.priority.ai_priority_score,
        )
        return issue

    async def _resolve_category(
        self, db: AsyncSession, code: str
    ) -> IssueCategory | None:
        result = await db.execute(
            select(IssueCategory).where(IssueCategory.code == code)
        )
        return result.scalar_one_or_none()


issue_ai_pipeline = IssueAIPipeline()

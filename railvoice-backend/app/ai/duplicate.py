from __future__ import annotations

import uuid
from dataclasses import dataclass

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

import re

from app.ai.embeddings import embedding_service, SYNONYM_GROUPS
from app.core.config import settings


def effective_duplicate_threshold() -> float:
    if settings.openai_api_key:
        return settings.duplicate_similarity_threshold
    return settings.local_duplicate_similarity_threshold


def _token_jaccard(text_a: str, text_b: str) -> float:
    ta = set(re.findall(r"[a-z0-9]+", text_a.lower()))
    tb = set(re.findall(r"[a-z0-9]+", text_b.lower()))
    expanded_a: set[str] = set()
    expanded_b: set[str] = set()
    for t in ta:
        expanded_a.add(t)
        for group in SYNONYM_GROUPS:
            if t in group:
                expanded_a |= group
    for t in tb:
        expanded_b.add(t)
        for group in SYNONYM_GROUPS:
            if t in group:
                expanded_b |= group
    if not expanded_a or not expanded_b:
        return 0.0
    return len(expanded_a & expanded_b) / len(expanded_a | expanded_b)


def _combined_similarity(
    embedding_a: list[float],
    embedding_b: list[float],
    text_a: str,
    text_b: str,
) -> float:
    cosine = embedding_service.cosine_similarity(embedding_a, embedding_b)
    if embedding_service.uses_openai:
        return cosine
    jaccard = _token_jaccard(text_a, text_b)
    return 0.35 * cosine + 0.65 * jaccard
from app.core.enums import DUPLICATE_SEARCH_EXCLUDED
from app.models.issue import Issue


@dataclass
class SimilarIssue:
    issue: Issue
    similarity: float


class DuplicateDetectionService:
    async def find_similar(
        self,
        db: AsyncSession,
        description: str,
        station_id: uuid.UUID,
        title: str | None = None,
        limit: int = 5,
    ) -> list[SimilarIssue]:
        query_text = f"{title or ''} {description}".strip()
        embedding = (await embedding_service.embed([query_text]))[0]
        threshold = effective_duplicate_threshold()

        result = await db.execute(
            select(Issue).where(
                Issue.station_id == station_id,
                Issue.embedding.isnot(None),
                Issue.is_public.is_(True),
                Issue.status.notin_([s.value for s in DUPLICATE_SEARCH_EXCLUDED]),
            )
        )
        issues = result.scalars().all()

        similar: list[SimilarIssue] = []
        for issue in issues:
            issue_embedding = embedding_service.to_list(issue.embedding)
            if not issue_embedding:
                continue
            issue_text = f"{issue.title or ''} {issue.description}".strip()
            sim = _combined_similarity(embedding, issue_embedding, query_text, issue_text)
            if sim >= threshold:
                similar.append(SimilarIssue(issue=issue, similarity=sim))

        similar.sort(key=lambda item: item.similarity, reverse=True)
        return similar[:limit]


duplicate_detection_service = DuplicateDetectionService()

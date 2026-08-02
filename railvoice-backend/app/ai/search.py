from __future__ import annotations

import uuid
from typing import Sequence

from sqlalchemy import or_, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.ai.embeddings import embedding_service
from app.ai.schemas import SearchResult
from app.models.issue import Issue


def reciprocal_rank_fusion(
    rankings: list[list[tuple[uuid.UUID, float]]],
    k: int = 60,
) -> dict[uuid.UUID, float]:
    """Merge multiple ranked lists using RRF."""
    scores: dict[uuid.UUID, float] = {}
    for ranking in rankings:
        for rank, (item_id, _) in enumerate(ranking, start=1):
            scores[item_id] = scores.get(item_id, 0.0) + 1.0 / (k + rank)
    return scores


class HybridSearchService:
    async def search(
        self,
        db: AsyncSession,
        query: str,
        *,
        station_id: uuid.UUID | None = None,
        limit: int = 20,
    ) -> list[SearchResult]:
        query = query.strip()
        if len(query) < 2:
            return []

        embedding = (await embedding_service.embed([query]))[0]

        base_filter = [Issue.is_public.is_(True), Issue.embedding.isnot(None)]
        if station_id:
            base_filter.append(Issue.station_id == station_id)

        cosine_dist = Issue.embedding.cosine_distance(embedding)
        result = await db.execute(
            select(Issue, (1.0 - cosine_dist).label("similarity"))
            .where(*base_filter)
            .order_by(cosine_dist.asc())
            .limit(100)
        )
        rows = result.all()
        issues = [row[0] for row in rows]
        issue_sim_map = {row[0].id: float(row[1]) for row in rows}

        semantic_ranking: list[tuple[uuid.UUID, float]] = []
        keyword_ranking: list[tuple[uuid.UUID, float]] = []
        tokens = set(query.lower().split())

        for issue in issues:
            sim = issue_sim_map.get(issue.id, 0.0)
            if sim > 0.3:
                semantic_ranking.append((issue.id, sim))

            text = f"{issue.title or ''} {issue.description}".lower()
            keyword_hits = sum(1 for t in tokens if t in text)
            if keyword_hits:
                keyword_ranking.append((issue.id, keyword_hits / max(len(tokens), 1)))

        semantic_ranking.sort(key=lambda x: x[1], reverse=True)
        keyword_ranking.sort(key=lambda x: x[1], reverse=True)

        fused = reciprocal_rank_fusion([semantic_ranking, keyword_ranking])
        if not fused:
            return []

        issue_map = {i.id: i for i in issues}
        results: list[SearchResult] = []
        for issue_id, score in sorted(fused.items(), key=lambda x: x[1], reverse=True)[:limit]:
            issue = issue_map.get(issue_id)
            if not issue:
                continue
            sem_score = next((s for i, s in semantic_ranking if i == issue_id), 0.0)
            kw_score = next((s for i, s in keyword_ranking if i == issue_id), 0.0)
            match_type = "hybrid"
            if sem_score > kw_score:
                match_type = "semantic"
            elif kw_score > sem_score:
                match_type = "keyword"
            results.append(
                SearchResult(
                    issue_id=str(issue_id),
                    relevance_score=round(score, 4),
                    match_type=match_type,
                )
            )
        return results


hybrid_search_service = HybridSearchService()

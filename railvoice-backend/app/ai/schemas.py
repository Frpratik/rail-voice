from __future__ import annotations

from dataclasses import dataclass, field


@dataclass
class CategoryPrediction:
    category_code: str
    subcategory_code: str | None
    confidence: float
    severity: int


@dataclass
class SpamPrediction:
    spam_score: float
    fake_score: float
    is_auto_hold: bool
    reasons: list[str] = field(default_factory=list)


@dataclass
class PriorityPrediction:
    ai_priority_score: float
    is_emergency: bool
    factors: dict[str, float]


@dataclass
class IssueAIAnalysis:
    embedding: list[float]
    embedding_model: str
    category: CategoryPrediction
    spam: SpamPrediction
    priority: PriorityPrediction
    summary: str | None = None


@dataclass
class SearchResult:
    issue_id: str
    relevance_score: float
    match_type: str  # semantic | keyword | hybrid

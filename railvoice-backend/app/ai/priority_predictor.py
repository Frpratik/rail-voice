from __future__ import annotations

from app.ai.schemas import CategoryPrediction, PriorityPrediction, SpamPrediction


class PriorityPredictor:
    """Combines AI signals into a 0–1 priority score for official triage."""

    def predict(
        self,
        *,
        category: CategoryPrediction,
        spam: SpamPrediction,
        severity: int,
        description: str,
    ) -> PriorityPrediction:
        factors: dict[str, float] = {}

        factors["category_confidence"] = category.confidence * 0.15
        factors["severity"] = (severity / 5.0) * 0.35
        factors["spam_inverse"] = (1.0 - spam.spam_score) * 0.2
        factors["fake_inverse"] = (1.0 - spam.fake_score) * 0.15

        detail_bonus = min(len(description) / 500.0, 1.0) * 0.15
        factors["detail_richness"] = detail_bonus

        score = min(sum(factors.values()), 1.0)
        is_emergency = severity >= 5

        if is_emergency:
            score = min(score + 0.15, 1.0)

        return PriorityPrediction(
            ai_priority_score=round(score, 4),
            is_emergency=is_emergency,
            factors={k: round(v, 4) for k, v in factors.items()},
        )


priority_predictor = PriorityPredictor()

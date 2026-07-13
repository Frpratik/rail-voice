"""Dataset-driven evaluation for AI duplicate detection accuracy."""

from __future__ import annotations

import pytest

from app.ai.duplicate import _combined_similarity, effective_duplicate_threshold
from app.ai.embeddings import embedding_service


def _similarity(text_a: str, text_b: str) -> float:
    emb_a = embedding_service._local_embedding(text_a)
    emb_b = embedding_service._local_embedding(text_b)
    return _combined_similarity(emb_a, emb_b, text_a, text_b)


def _evaluate_pairs(pairs: list[dict]) -> dict:
    threshold = effective_duplicate_threshold()
    stats = {"tp": 0, "tn": 0, "fp": 0, "fn": 0, "threshold": threshold}

    for pair in pairs:
        sim = _similarity(pair["issue_a"], pair["issue_b"])
        predicted_dup = sim >= threshold
        expected_dup = pair["is_duplicate"]

        if expected_dup and predicted_dup:
            stats["tp"] += 1
        elif not expected_dup and not predicted_dup:
            stats["tn"] += 1
        elif not expected_dup and predicted_dup:
            stats["fp"] += 1
        else:
            stats["fn"] += 1
    return stats


def test_evaluate_duplicate_pairs_local_tier(ai_duplicate_pairs):
    """Local-tier pairs must pass without OpenAI (CI/dev)."""
    pairs = [p for p in ai_duplicate_pairs["pairs"] if p.get("tier") == "local"]
    stats = _evaluate_pairs(pairs)

    assert stats["fp"] == 0, "Local tier must have zero false positives"
    assert stats["fn"] == 0, "Local tier must have zero false negatives"
    assert stats["tp"] >= 1


@pytest.mark.skipif(
    not embedding_service.uses_openai,
    reason="Production-tier eval requires OPENAI_API_KEY",
)
def test_evaluate_duplicate_pairs_production_tier(ai_duplicate_pairs):
    """Full paraphrase set — run in staging/production with OpenAI embeddings."""
    pairs = [p for p in ai_duplicate_pairs["pairs"] if p.get("tier") == "production"]
    stats = _evaluate_pairs(pairs)

    precision = stats["tp"] / (stats["tp"] + stats["fp"]) if (stats["tp"] + stats["fp"]) else 1.0
    recall = stats["tp"] / (stats["tp"] + stats["fn"]) if (stats["tp"] + stats["fn"]) else 1.0

    assert precision >= 0.85
    assert recall >= 0.85

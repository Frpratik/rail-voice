from __future__ import annotations

import math
from datetime import datetime, timezone

from app.core.config import settings


def freshness_decay(created_at: datetime, lambda_: float = 0.01) -> float:
    hours = (datetime.now(timezone.utc) - created_at).total_seconds() / 3600
    return math.exp(-lambda_ * max(hours, 0))


def compute_priority_score(
    support_count: int | None,
    severity: int | None,
    created_at: datetime,
    trending_score: float | None = 0.0,
    ai_priority_score: float | None = 0.5,
    weights: dict | None = None,
) -> float:
    w = weights or {
        "support": 0.25,
        "severity": 0.25,
        "fresh": 0.15,
        "trend": 0.20,
        "ai": 0.15,
    }
    norm_support = min((support_count or 0) / 100.0, 1.0)
    severity_norm = (severity or 3) / 5.0
    fresh = freshness_decay(created_at)
    trend_norm = min(float(trending_score or 0), 1.0)
    ai_score = float(ai_priority_score if ai_priority_score is not None else 0.5)

    score = (
        w["support"] * norm_support
        + w["severity"] * severity_norm
        + w["fresh"] * fresh
        + w["trend"] * trend_norm
        + w["ai"] * ai_score
    ) * 100

    if (severity or 0) >= 5:
        score += 20
    return round(score, 2)


def simple_categorize(description: str) -> tuple[str, int]:
    text = description.lower()
    rules = [
        (["dustbin", "garbage", "waste", "dirty", "clean"], "station_infrastructure", 3),
        (["lift", "elevator", "escalator", "ramp"], "accessibility", 4),
        (["unsafe", "safety", "women", "harassment", "cctv"], "safety_security", 5),
        (["seat", "fan", "coach", "overcrowd", "train"], "train_coach", 3),
        (["ticket", "counter", "parking", "toilet", "water"], "facilities", 3),
        (["late", "delay", "announcement", "platform"], "operations", 2),
    ]
    for keywords, code, severity in rules:
        if any(k in text for k in keywords):
            return code, severity
    return "other", 3


def spam_score_heuristic(description: str) -> float:
    text = description.lower()
    if len(text) < 20:
        return 0.9
    spam_signals = ["http://", "https://", "buy now", "click here", "free money"]
    hits = sum(1 for s in spam_signals if s in text)
    return min(hits * 0.35, 0.95)

from __future__ import annotations

import math
from datetime import datetime, timezone


def compute_trending_score(
    support_count: int,
    supports_24h: int,
    supports_7d: int,
    created_at: datetime,
) -> float:
    """
    Trending = support velocity weighted by recency and volume.
    Returns normalized score 0–1.
    """
    if support_count == 0:
        return 0.0

    velocity_24h = supports_24h / max(support_count, 1)
    velocity_7d = supports_7d / max(support_count, 1)

    age_hours = (datetime.now(timezone.utc) - created_at).total_seconds() / 3600
    recency = math.exp(-0.02 * age_hours)  # decay over ~2 days

    raw = (
        velocity_24h * 0.5
        + velocity_7d * 0.2
        + math.log1p(support_count) / 10.0 * 0.2
        + recency * 0.1
    )
    return round(min(raw, 1.0), 4)

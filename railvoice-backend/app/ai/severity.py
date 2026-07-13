from __future__ import annotations

import re

from app.ai.schemas import CategoryPrediction

EMERGENCY_KEYWORDS = [
    "emergency",
    "urgent",
    "immediate",
    "stampede",
    "fire",
    "electrocuted",
    "accident",
    "injured",
    "collapse",
    "live wire",
]

HIGH_SEVERITY_KEYWORDS = [
    "unsafe",
    "danger",
    "harassment",
    "women safety",
    "broken bridge",
    "no lighting",
    "dark platform",
]


class SeverityPredictor:
    def predict(self, text: str, category: CategoryPrediction) -> int:
        lower = text.lower()
        if any(kw in lower for kw in EMERGENCY_KEYWORDS):
            return 5
        if any(kw in lower for kw in HIGH_SEVERITY_KEYWORDS):
            return max(category.severity, 4)
        if category.severity >= 4:
            return category.severity
        # Exclamation and caps boost
        if text.count("!") >= 2 or len(re.findall(r"\b[A-Z]{4,}\b", text)) >= 2:
            return min(category.severity + 1, 5)
        return category.severity


severity_predictor = SeverityPredictor()

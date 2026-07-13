from __future__ import annotations

import re

from app.core.config import settings
from app.ai.schemas import SpamPrediction

SPAM_PHRASES = [
    "http://",
    "https://",
    "www.",
    "buy now",
    "click here",
    "free money",
    "crypto",
    "whatsapp me",
    "call me at",
]

FAKE_INDICATORS = [
    "never happened",
    "just testing",
    "fake report",
    "ignore this",
    "as a joke",
    "lol test",
]


class SpamDetector:
    def predict(
        self,
        text: str,
        *,
        is_anonymous: bool = False,
        has_photo: bool = False,
    ) -> SpamPrediction:
        lower = text.lower()
        reasons: list[str] = []
        spam_score = 0.0
        fake_score = 0.0

        if len(text.strip()) < 20:
            spam_score += 0.5
            reasons.append("description_too_short")

        spam_hits = sum(1 for p in SPAM_PHRASES if p in lower)
        if spam_hits:
            spam_score += min(spam_hits * 0.25, 0.75)
            reasons.append("spam_phrases")

        if re.search(r"(.)\1{6,}", text):
            spam_score += 0.3
            reasons.append("repeated_characters")

        fake_hits = sum(1 for p in FAKE_INDICATORS if p in lower)
        if fake_hits:
            fake_score += min(fake_hits * 0.4, 0.9)
            reasons.append("fake_indicators")

        if is_anonymous and not has_photo and len(text) < 60:
            fake_score += 0.15
            reasons.append("anonymous_short_no_photo")

        spam_score = min(spam_score, 1.0)
        fake_score = min(fake_score, 1.0)
        combined = max(spam_score, fake_score * 0.9)

        return SpamPrediction(
            spam_score=round(spam_score, 4),
            fake_score=round(fake_score, 4),
            is_auto_hold=combined >= settings.spam_auto_hold_threshold,
            reasons=reasons,
        )


spam_detector = SpamDetector()

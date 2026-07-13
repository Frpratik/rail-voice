from __future__ import annotations

import re

from app.ai.schemas import CategoryPrediction

# (keywords, category_code, subcategory_code, default_severity)
CATEGORY_RULES: list[tuple[list[str], str, str | None, int]] = [
    (["dustbin", "garbage", "waste", "litter", "dirty platform"], "station_infrastructure", "dustbins_waste", 3),
    (["clean", "filthy", "smell", "stink"], "station_infrastructure", "platform_cleanliness", 3),
    (["light", "dark", "bulb", "lighting"], "station_infrastructure", "platform_cleanliness", 3),
    (["leak", "leakage", "water on"], "station_infrastructure", "platform_cleanliness", 4),
    (["lift", "elevator"], "accessibility", "lifts_escalators", 4),
    (["escalator", "escalator"], "accessibility", "lifts_escalators", 4),
    (["ramp", "wheelchair", "tactile"], "accessibility", "lifts_escalators", 3),
    (["unsafe", "danger", "hazard"], "safety_security", None, 5),
    (["women", "harassment", "molest", "eve tease"], "safety_security", "womens_safety", 5),
    (["cctv", "camera", "security"], "safety_security", None, 4),
    (["seat", "broken seat"], "train_coach", "overcrowding", 3),
    (["fan", "ac ", "air condition"], "train_coach", None, 3),
    (["overcrowd", "packed", "rush"], "train_coach", "overcrowding", 4),
    (["coach", "compartment"], "train_coach", None, 3),
    (["ticket", "counter", "uts"], "facilities", "ticket_counter", 3),
    (["parking", "vehicle"], "facilities", None, 3),
    (["toilet", "washroom", "restroom"], "facilities", None, 4),
    (["drinking water", "water cooler"], "facilities", None, 3),
    (["late", "delay", "punctual"], "operations", "train_punctuality", 2),
    (["announcement", "pa system", "speaker"], "operations", None, 3),
    (["suggest", "improve", "should have"], "other", None, 2),
]


class IssueCategorizer:
    """Rule-based categorizer with confidence scoring (LLM-pluggable later)."""

    def predict(self, text: str, title: str | None = None) -> CategoryPrediction:
        combined = f"{title or ''} {text}".lower()
        tokens = set(re.findall(r"\w+", combined))

        best: CategoryPrediction | None = None
        best_hits = 0

        for keywords, cat_code, sub_code, severity in CATEGORY_RULES:
            hits = sum(1 for kw in keywords if kw in combined)
            if hits > best_hits:
                best_hits = hits
                confidence = min(0.55 + hits * 0.15, 0.95)
                best = CategoryPrediction(
                    category_code=cat_code,
                    subcategory_code=sub_code,
                    confidence=confidence,
                    severity=severity,
                )

        if best and best_hits > 0:
            return best

        return CategoryPrediction(
            category_code="other",
            subcategory_code=None,
            confidence=0.4,
            severity=3,
        )


issue_categorizer = IssueCategorizer()

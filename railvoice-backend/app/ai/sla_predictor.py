from __future__ import annotations

import logging
from datetime import datetime, timezone
from typing import Any

from app.models.issue import Issue

logger = logging.getLogger(__name__)

CATEGORY_SLA_TARGET_HOURS = {
    "safety_security": 12.0,
    "womens_safety": 6.0,
    "medical_emergency": 4.0,
    "platform_cleanliness": 24.0,
    "station_infrastructure": 48.0,
    "lifts_escalators": 36.0,
    "ticket_counter": 24.0,
}
DEFAULT_SLA_HOURS = 24.0


class SLAPredictorService:
    def predict_issue_sla_risk(
        self, issue: Issue, station_open_count: int = 0
    ) -> dict[str, Any]:
        """Predict SLA breach risk percentage and remaining window for an active grievance."""
        now = datetime.now(timezone.utc)
        created_at = issue.created_at
        if created_at.tzinfo is None:
            created_at = created_at.replace(tzinfo=timezone.utc)

        elapsed_hours = max(0.0, (now - created_at).total_seconds() / 3600.0)

        # Lookup SLA target hours
        category = getattr(issue, "category", None)
        category_code = category.code.lower() if category and getattr(category, "code", None) else ""
        target_hours = CATEGORY_SLA_TARGET_HOURS.get(category_code, DEFAULT_SLA_HOURS)

        # Calculate time ratio
        time_ratio = elapsed_hours / target_hours

        # Workload load factor (more open issues at station increases risk)
        load_factor = 1.0 + min(0.5, (station_open_count * 0.05))

        # Calculated risk score percentage
        risk_score_pct = min(100.0, round(time_ratio * 100.0 * load_factor, 1))

        # Calculate hours remaining
        hours_remaining = max(0.0, round(target_hours - elapsed_hours, 1))

        # Risk classification
        if risk_score_pct >= 85.0 or hours_remaining <= 2.0:
            risk_level = "critical"
        elif risk_score_pct >= 65.0:
            risk_level = "high"
        elif risk_score_pct >= 40.0:
            risk_level = "medium"
        else:
            risk_level = "low"

        station = getattr(issue, "station", None)
        upvote_count = getattr(issue, "upvote_count", 0) or 0

        risk_factors = []
        if time_ratio >= 0.75:
            risk_factors.append("Time window 75% elapsed")
        if station_open_count >= 5:
            risk_factors.append(f"High station workload ({station_open_count} open issues)")
        if upvote_count >= 10:
            risk_factors.append(f"High community impact ({upvote_count} upvotes)")

        return {
            "issue_id": str(issue.id),
            "issue_number": getattr(issue, "issue_number", "RV-UNK"),
            "title": getattr(issue, "title", ""),
            "station_name": station.name if station and getattr(station, "name", None) else "Unknown",
            "station_code": station.code if station and getattr(station, "code", None) else "UNK",
            "category_code": category_code,
            "status": getattr(issue, "status", "submitted"),
            "target_sla_hours": target_hours,
            "elapsed_hours": round(elapsed_hours, 1),
            "hours_remaining": hours_remaining,
            "risk_score_pct": risk_score_pct,
            "risk_level": risk_level,
            "risk_factors": risk_factors,
        }


sla_predictor = SLAPredictorService()

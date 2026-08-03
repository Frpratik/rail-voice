from datetime import datetime, timedelta, timezone

import pytest
from httpx import AsyncClient

from app.ai.sla_predictor import sla_predictor
from app.models.issue import Issue

API = "/api/v1"


def test_sla_predictor_calculation():
    now = datetime.now(timezone.utc)

    # Mock issue created 20 hours ago for a 24h category
    issue = Issue(
        id="00000000-0000-0000-0000-000000000001",
        issue_number="RV-TEST-001",
        title="Test Water Leakage",
        created_at=now - timedelta(hours=20),
        status="submitted",
    )

    risk_data = sla_predictor.predict_issue_sla_risk(issue, station_open_count=5)

    assert risk_data["risk_score_pct"] > 70.0
    assert risk_data["risk_level"] in {"high", "critical"}
    assert risk_data["hours_remaining"] <= 4.0
    assert len(risk_data["risk_factors"]) >= 1


@pytest.mark.asyncio
async def test_get_sla_risk_radar_endpoint(client: AsyncClient, admin_headers: dict):
    res = await client.get(f"{API}/admin/sla-risk-radar", headers=admin_headers)
    assert res.status_code == 200
    assert "data" in res.json()
    data = res.json()["data"]
    assert isinstance(data, list)

import uuid
import pytest
from httpx import AsyncClient
from app.db.session import async_session_factory
from app.models.dispatch import WorkforceStaff

API = "/api/v1"

@pytest.mark.asyncio
async def test_get_dispatch_roster(client: AsyncClient):
    async with async_session_factory() as db:
        staff = WorkforceStaff(
            id=uuid.uuid4(),
            full_name="Test Staff Personnel",
            skill_category="housekeeping",
            contact_number="+919999000011",
            status="available",
            shift_start="08:00",
            shift_end="16:00",
            is_active=True,
        )
        db.add(staff)
        await db.commit()

    response = await client.get(f"{API}/admin/dispatch/roster")
    assert response.status_code == 200
    data = response.json()["data"]
    assert "total_staff" in data
    assert "available_count" in data
    assert "staff_list" in data
    assert data["total_staff"] > 0

@pytest.mark.asyncio
async def test_get_dispatch_recommendations(client: AsyncClient):
    response = await client.get(f"{API}/admin/dispatch/recommendations")
    assert response.status_code == 200
    data = response.json()["data"]
    assert isinstance(data, list)

@pytest.mark.asyncio
async def test_auto_assign_dispatch(client: AsyncClient):
    response = await client.post(f"{API}/admin/dispatch/auto-assign")
    assert response.status_code == 200
    data = response.json()["data"]
    assert "dispatched_count" in data
    assert "assignments" in data

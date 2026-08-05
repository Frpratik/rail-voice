import asyncio
import uuid
from sqlalchemy import select
from app.db.session import async_session_factory
from app.models.dispatch import WorkforceStaff
from app.models.location import Station

INITIAL_STAFF = [
    {"full_name": "Ramesh Kumar", "skill_category": "housekeeping", "contact_number": "+919820011223", "shift_start": "06:00", "shift_end": "14:00"},
    {"full_name": "Suresh Patil", "skill_category": "housekeeping", "contact_number": "+919820011224", "shift_start": "14:00", "shift_end": "22:00"},
    {"full_name": "Vikram Singh", "skill_category": "electrical", "contact_number": "+919820011225", "shift_start": "08:00", "shift_end": "16:00"},
    {"full_name": "Anil Deshmukh", "skill_category": "electrical", "contact_number": "+919820011226", "shift_start": "16:00", "shift_end": "00:00"},
    {"full_name": "Mahesh Shinde", "skill_category": "mechanical", "contact_number": "+919820011227", "shift_start": "09:00", "shift_end": "17:00"},
    {"full_name": "Rajesh Sharma", "skill_category": "mechanical", "contact_number": "+919820011228", "shift_start": "09:00", "shift_end": "17:00"},
    {"full_name": "RPF Constable Inspector Yadav", "skill_category": "safety", "contact_number": "+919820011229", "shift_start": "00:00", "shift_end": "23:59"},
    {"full_name": "Sunita Verma (OBHS Head)", "skill_category": "housekeeping", "contact_number": "+919820011230", "shift_start": "06:00", "shift_end": "18:00"},
]

async def seed_dispatch():
    async with async_session_factory() as db:
        res = await db.execute(select(WorkforceStaff))
        existing = res.scalars().all()
        if len(existing) >= len(INITIAL_STAFF):
            print(f"Workforce staff already seeded ({len(existing)} staff members found).")
            return

        station_res = await db.execute(select(Station))
        stations = list(station_res.scalars().all())

        for idx, staff_data in enumerate(INITIAL_STAFF):
            assigned_station = stations[idx % len(stations)] if stations else None
            staff = WorkforceStaff(
                id=uuid.uuid4(),
                full_name=staff_data["full_name"],
                skill_category=staff_data["skill_category"],
                contact_number=staff_data["contact_number"],
                assigned_station_id=assigned_station.id if assigned_station else None,
                status="available",
                shift_start=staff_data["shift_start"],
                shift_end=staff_data["shift_end"],
                is_active=True,
            )
            db.add(staff)

        await db.commit()
        print(f"Successfully seeded {len(INITIAL_STAFF)} workforce staff members!")

if __name__ == "__main__":
    asyncio.run(seed_dispatch())

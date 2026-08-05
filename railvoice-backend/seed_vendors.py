import asyncio
from datetime import datetime, timedelta, timezone
from sqlalchemy import select
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker

from app.core.config import settings
from app.models.vendor import VendorContract
from app.models.issue import Issue
from app.models.location import Station, IssueCategory

from app.db.session import async_session_factory

async def seed():
    async with async_session_factory() as db:
        # 1. Get any station and category
        st_res = await db.execute(select(Station))
        station = st_res.scalars().first()
        
        cat_res = await db.execute(select(IssueCategory))
        category = cat_res.scalars().first()
        
        if not station or not category:
            print("No stations or categories found!")
            return

        # 2. Check if contract exists, otherwise create
        con_res = await db.execute(select(VendorContract).where(VendorContract.contract_code == "WR-SANI-001"))
        contract = con_res.scalars().first()
        
        if not contract:
            contract = VendorContract(
                vendor_name="CleanTech Solutions Pvt Ltd",
                contract_code="WR-SANI-001",
                station_id=station.id,
                category_id=category.id,
                penalty_per_sla_hour=1000.00,
                max_penalty_cap=10000.00,
                is_active=True
            )
            db.add(contract)
            await db.commit()
            await db.refresh(contract)
            print("Created Vendor Contract:", contract.id)
        else:
            print("Contract already exists:", contract.id)

        # 3. Find an issue to backdate
        iss_res = await db.execute(
            select(Issue)
            .where(Issue.station_id == station.id)
            .where(Issue.category_id == category.id)
            .where(Issue.status != "RESOLVED")
        )
        issue = iss_res.scalars().first()
        
        if issue:
            print("Found Issue:", issue.id)
            # Backdate it by 6 hours
            issue.created_at = datetime.now(timezone.utc).replace(tzinfo=None) - timedelta(hours=6)
            await db.commit()
            print(f"Backdated issue {issue.id} to 6 hours ago")
        else:
            print("No open issue found for this station and category. Please create one.")

if __name__ == "__main__":
    asyncio.run(seed())

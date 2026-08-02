from collections.abc import AsyncGenerator

from sqlalchemy.ext.asyncio import AsyncAttrs, AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy.orm import DeclarativeBase

from app.core.config import settings


class Base(AsyncAttrs, DeclarativeBase):
    pass


import sys
from sqlalchemy.pool import NullPool

pool_kwargs = (
    {"poolclass": NullPool}
    if "pytest" in sys.modules
    else {
        "pool_size": 10,
        "max_overflow": 20,
        "pool_recycle": 1800,
        "pool_pre_ping": True,
    }
)
engine = create_async_engine(settings.database_url, echo=settings.debug, **pool_kwargs)
async_session_factory = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)


async def get_db() -> AsyncGenerator[AsyncSession, None]:
    async with async_session_factory() as session:
        async with session.begin():
            yield session

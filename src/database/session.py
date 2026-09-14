from typing import AsyncGenerator

from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker
from sqlalchemy.ext.asyncio.session import AsyncSession

from config.settings import settings

db_engine = create_async_engine(settings.DB_URL, echo=True)

SessionLocal = async_sessionmaker(
    db_engine, expire_on_commit=False, autoflush=False, autocommit=False
)


async def get_db() -> AsyncGenerator[AsyncSession, None]:
    async with SessionLocal() as session:
        yield session

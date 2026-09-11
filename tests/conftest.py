from typing import AsyncGenerator

import pytest
from httpx import AsyncClient, ASGITransport
from sqlalchemy import NullPool
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine, async_sessionmaker

from config.dependencies import get_accounts_email_notificator
from config.settings import settings
from database.models.base import Base
from main import app
from database.session import get_db
from mocks.email import MockEmailSender

db_engine = create_async_engine(settings.DB_URL, poolclass=NullPool)
SessionLocal = async_sessionmaker(
    bind=db_engine, expire_on_commit=False, autoflush=False
)


@pytest.fixture()
async def db_session() -> AsyncGenerator[AsyncSession, None]:
    async with SessionLocal() as session:
        yield session


@pytest.fixture()
async def client(db_session):
    async def override_get_db():
        yield db_session

    app.dependency_overrides[get_db] = override_get_db

    transport = ASGITransport(app=app)

    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        yield ac

    app.dependency_overrides.pop(get_db, None)


@pytest.fixture(autouse=True)
async def reset_db_before_every_test():
    async with db_engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)
        await conn.run_sync(Base.metadata.create_all)
    yield


@pytest.fixture(autouse=True)
def override_email_dependency():
    app.dependency_overrides[get_accounts_email_notificator] = lambda: MockEmailSender()
    yield
    app.dependency_overrides.pop(get_accounts_email_notificator, None)

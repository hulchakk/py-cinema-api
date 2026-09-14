from decimal import Decimal
from typing import AsyncGenerator

import pytest
from httpx import AsyncClient, ASGITransport
from sqlalchemy import NullPool
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine, async_sessionmaker

from config.dependencies import get_accounts_email_notificator, get_jwt_auth_manager
from config.settings import settings
from database.models.accounts import UserGroupModel, UserGroupEnum, UserModel
from database.models.base import Base
from database.models.movies import (
    StarModel,
    GenreModel,
    DirectorModel,
    CertificationModel,
    MovieModel,
)
from security.dependencies import get_current_user
from tests.utils import get_default_user_group
from main import app
from database.session import get_db
from mocks.email import MockEmailSender
from mocks.token_manager import MockJWTAuthManager

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
async def reset_db_before_every_test(db_session):
    async with db_engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)
        await conn.run_sync(Base.metadata.create_all)

    user_group = UserGroupModel(
        name=UserGroupEnum.USER,
    )
    moderator_group = UserGroupModel(
        name=UserGroupEnum.MODERATOR,
    )
    admin_group = UserGroupModel(
        name=UserGroupEnum.ADMIN,
    )

    db_session.add(user_group)
    db_session.add(moderator_group)
    db_session.add(admin_group)

    await db_session.commit()

    yield


@pytest.fixture(autouse=True)
def override_email_dependency():
    app.dependency_overrides[get_accounts_email_notificator] = lambda: MockEmailSender()
    yield
    app.dependency_overrides.pop(get_accounts_email_notificator, None)


@pytest.fixture(autouse=True)
def override_get_token_manager_dependency(db_session):
    app.dependency_overrides[get_jwt_auth_manager] = lambda: MockJWTAuthManager()
    yield
    app.dependency_overrides.pop(get_jwt_auth_manager, None)


@pytest.fixture
async def default_user(db_session: AsyncSession) -> UserModel:
    group = await get_default_user_group(db_session)

    user = UserModel.create(
        email="user@example.com", raw_password="1Qazcde3", group_id=group.id
    )

    user.is_active = True

    db_session.add(user)
    await db_session.commit()
    await db_session.refresh(user)

    return user


@pytest.fixture
async def override_get_current_user_dependency(default_user):
    app.dependency_overrides[get_current_user] = lambda: default_user
    yield
    app.dependency_overrides.pop(get_current_user, None)


@pytest.fixture
async def populate_movies(db_session) -> None:
    star = StarModel(name="Star")
    genre = GenreModel(name="Genre")
    director = DirectorModel(name="Director")
    certification = CertificationModel(name="Certification")

    for el in (
        star,
        genre,
        director,
        certification,
    ):
        db_session.add(el)

    await db_session.flush()

    for i in range(1, 11):
        movie = MovieModel(
            name=f"Movie {i}",
            year=2026,
            time=90,
            imdb=4.0,
            votes=10,
            description=f"Movie {i}",
            price=Decimal(f"{i}.50"),
            certification_id=certification.id,
        )

        movie.directors.append(director)
        movie.genres.append(genre)
        movie.stars.append(star)

        db_session.add(movie)

    await db_session.commit()

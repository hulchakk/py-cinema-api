import pytest
from httpx import AsyncClient, Response
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import joinedload

from database.models.accounts import (
    UserModel,
    UserGroupEnum,
    ActivationTokenModel,
    UserGroupModel,
    RefreshTokenModel,
)


async def _get_default_user_group(db_session: AsyncSession) -> UserGroupModel:
    stmt = select(UserGroupModel).where(UserGroupModel.name == UserGroupEnum.USER)
    user_group = await db_session.scalar(stmt)

    assert user_group is not None

    return user_group


class TestRegisterAndActivateEndpoints:
    user_email = "user@example.com"
    register_endpoint = "/api/v1/accounts/register"
    activate_endpoint = "/api/v1/accounts/activate"

    async def _register_default_user(self, client: AsyncClient) -> Response:
        response = await client.post(
            self.register_endpoint,
            json={"email": self.user_email, "password": "1Qazcde3"},
        )

        return response

    async def test_register_user(
        self, db_session: AsyncSession, client: AsyncClient
    ) -> None:
        response = await self._register_default_user(client)
        assert response.status_code == 201

        stmt = (
            select(UserModel)
            .where(UserModel.email == self.user_email)
            .options(joinedload(UserModel.group))
        )
        user = await db_session.scalar(stmt)

        assert user is not None
        assert user.is_active == False
        assert user.group.name == UserGroupEnum.USER

    async def test_register_existing_user(
        self, db_session: AsyncSession, client: AsyncClient
    ) -> None:
        user_group = await _get_default_user_group(db_session)

        user = UserModel.create(
            email=self.user_email,
            raw_password="1Qazcde3",
            group_id=user_group.id,
        )

        db_session.add(user)

        await db_session.commit()

        response = await client.post(
            self.register_endpoint,
            json={"email": self.user_email, "password": "1Qazcde3"},
        )

        assert response.status_code == 409

    async def test_register_and_activate_user(
        self, db_session: AsyncSession, client: AsyncClient
    ) -> None:
        response = await self._register_default_user(client)

        assert response.status_code == 201

        stmt = (
            select(UserModel)
            .where(UserModel.email == self.user_email)
            .options(joinedload(UserModel.activation_token))
        )
        user = await db_session.scalar(stmt)

        assert user.activation_token is not None

        response = await client.post(
            self.activate_endpoint,
            json={"email": self.user_email, "token": user.activation_token.token},
        )

        assert response.status_code == 200

        await db_session.refresh(user)

        assert user.is_active == True

        stmt = select(ActivationTokenModel).where(
            ActivationTokenModel.user_id == user.id
        )
        token = await db_session.scalar(stmt)

        assert token is None

    async def test_activate_already_activated_user(
        self, db_session: AsyncSession, client: AsyncClient
    ) -> None:
        response = await self._register_default_user(client)

        assert response.status_code == 201

        stmt = select(UserModel).where(UserModel.email == self.user_email)
        user = await db_session.scalar(stmt)

        user.is_active = True

        await db_session.commit()

        stmt = select(ActivationTokenModel).where(
            ActivationTokenModel.user_id == user.id
        )
        token = await db_session.scalar(stmt)

        assert token is not None

        response = await client.post(
            self.activate_endpoint,
            json={"email": self.user_email, "token": token.token},
        )

        assert response.status_code == 400

    async def test_invalid_activation_token(
        self, db_session: AsyncSession, client: AsyncClient
    ) -> None:
        response = await self._register_default_user(client)

        assert response.status_code == 201

        response = await client.post(
            self.activate_endpoint,
            json={"email": self.user_email, "token": "123"},
        )

        assert response.status_code == 400

    async def test_activate_nonexistent_user(
        self, db_session: AsyncSession, client: AsyncClient
    ) -> None:
        response = await client.post(
            self.activate_endpoint,
            json={"email": self.user_email, "token": "123"},
        )

        assert response.status_code == 400


class TestLoginEndpoint:
    user_email = "user@example.com"
    user_password = "1Qazcde3"
    login_endpoint = "/api/v1/accounts/login"

    async def _login_default_user(self, client: AsyncClient) -> Response:
        response = await client.post(
            self.login_endpoint,
            data={"username": self.user_email, "password": self.user_password},
        )
        return response

    async def test_successful_login(
        self, client: AsyncClient, db_session: AsyncSession
    ) -> None:
        user_group = await _get_default_user_group(db_session)

        user = UserModel.create(
            email=self.user_email,
            raw_password=self.user_password,
            group_id=user_group.id,
        )
        user.is_active = True

        db_session.add(user)
        await db_session.commit()

        response = await self._login_default_user(client)
        assert response.status_code == 200

        assert response.json() == {
            "refresh_token": "mocked_refresh_token",
            "access_token": "mocked_access_token",
        }

        stmt = select(RefreshTokenModel).where(RefreshTokenModel.user_id == user.id)
        refresh_token = await db_session.scalar(stmt)

        assert refresh_token is not None
        assert refresh_token.token == "mocked_refresh_token"

    @pytest.mark.parametrize(
        "email,password",
        [
            ("wrong@example.com", "1Qazcde3"),
            ("user@example.com", "WrongPassword123"),
            ("wrong@example.com", "WrongPassword123"),
        ],
    )
    async def test_login_invalid_credentials(
        self, client: AsyncClient, db_session: AsyncSession, email: str, password: str
    ) -> None:
        group = await _get_default_user_group(db_session)
        user = UserModel.create(
            email=self.user_email,
            raw_password=self.user_password,
            group_id=group.id,
        )
        user.is_active = True
        db_session.add(user)
        await db_session.commit()

        response = await client.post(
            self.login_endpoint,
            data={"username": email, "password": password},
        )

        assert response.status_code == 401

    async def test_login_inactive_user(
        self, client: AsyncClient, db_session: AsyncSession
    ) -> None:
        group = await _get_default_user_group(db_session)

        user = UserModel.create(
            email=self.user_email,
            raw_password=self.user_password,
            group_id=group.id,
        )

        db_session.add(user)
        await db_session.commit()

        response = await self._login_default_user(client)

        assert response.status_code == 403

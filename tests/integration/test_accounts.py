from datetime import datetime, timedelta, timezone

import pytest
from httpx import AsyncClient, Response
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import joinedload

from database.models.accounts import (
    UserModel,
    UserGroupEnum,
    ActivationTokenModel,
    UserGroupModel,
    RefreshTokenModel,
    PasswordResetTokenModel,
)
from main import app
from security.dependencies import get_current_user


async def _get_default_user_group(db_session: AsyncSession) -> UserGroupModel:
    stmt = select(UserGroupModel).where(UserGroupModel.name == UserGroupEnum.USER)
    user_group = await db_session.scalar(stmt)

    assert user_group is not None

    return user_group


class TestRegisterAndActivateEndpoints:
    register_endpoint = "/api/v1/accounts/register"
    activate_endpoint = "/api/v1/accounts/activate"

    user_email = "user@example.com"

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
    login_endpoint = "/api/v1/accounts/login"

    user_email = "user@example.com"
    user_password = "1Qazcde3"

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


class TestRefreshEndpoint:
    refresh_endpoint = "/api/v1/accounts/refresh"

    user_email = "user@example.com"
    user_password = "1Qazcde3"

    async def test_successful_refresh(
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

        refresh_token_value = "mocked_refresh_token"
        db_refresh_token = RefreshTokenModel(
            token=refresh_token_value,
            user_id=user.id,
        )
        db_session.add(db_refresh_token)
        await db_session.commit()

        response = await client.post(
            self.refresh_endpoint,
            json={"refresh_token": refresh_token_value},
        )

        assert response.status_code == 200
        assert response.json() == {
            "access_token": "mocked_access_token",
        }

    async def test_refresh_token_not_found_in_db(
        self, client: AsyncClient, db_session: AsyncSession
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
            self.refresh_endpoint,
            json={"refresh_token": "non_existent_token_in_db"},
        )

        assert response.status_code == 400
        assert response.json()["detail"] == "Refresh token not found."

    async def test_refresh_for_inactive_user(
        self, client: AsyncClient, db_session: AsyncSession
    ) -> None:
        user_group = await _get_default_user_group(db_session)

        user = UserModel.create(
            email=self.user_email,
            raw_password=self.user_password,
            group_id=user_group.id,
        )
        user.is_active = False
        db_session.add(user)
        await db_session.commit()

        refresh_token_value = "mocked_refresh_token"
        db_refresh_token = RefreshTokenModel(
            token=refresh_token_value,
            user_id=user.id,
        )

        db_session.add(db_refresh_token)
        await db_session.commit()

        response = await client.post(
            self.refresh_endpoint,
            json={"refresh_token": refresh_token_value},
        )

        assert response.status_code == 404
        assert response.json()["detail"] == "User not found."

    async def test_refresh_nonexistent_user(self, client: AsyncClient) -> None:
        response = await client.post(
            self.refresh_endpoint,
            json={"refresh_token": "token_for_nonexistent_user"},
        )

        assert response.status_code == 404
        assert response.json()["detail"] == "User not found."

    async def test_refresh_with_invalid_token(self, client: AsyncClient) -> None:
        response = await client.post(
            self.refresh_endpoint,
            json={"refresh_token": "invalid_token"},
        )

        assert response.status_code == 400

    async def test_refresh_with_expired_token(self, client: AsyncClient) -> None:
        response = await client.post(
            self.refresh_endpoint,
            json={"refresh_token": "expired_token"},
        )

        assert response.status_code == 400


class TestResetPasswordEndpoints:
    request_password_reset_endpoint = "/api/v1/accounts/password/request-reset"
    reset_password_complete_endpoint = "/api/v1/accounts/password/reset-complete"

    user_email = "user@example.com"
    user_password = "1Qazcde3"
    user_new_password = "1NewPassword3"

    async def _create_default_user(self, db_session: AsyncSession) -> UserModel:
        group = await _get_default_user_group(db_session)

        user = UserModel.create(
            email=self.user_email,
            raw_password=self.user_password,
            group_id=group.id,
        )

        user.is_active = True

        db_session.add(user)
        await db_session.commit()
        await db_session.refresh(user)

        return user

    async def test_successful_request_password_reset(
        self, client: AsyncClient, db_session: AsyncSession
    ) -> None:
        user = await self._create_default_user(db_session)

        response = await client.post(
            self.request_password_reset_endpoint,
            json={
                "email": self.user_email,
            },
        )

        assert response.status_code == 200

        stmt = select(PasswordResetTokenModel).where(
            PasswordResetTokenModel.user_id == user.id
        )
        token = await db_session.scalar(stmt)

        assert token is not None

    async def test_request_password_reset_unexistent_user(
        self, client: AsyncClient, db_session: AsyncSession
    ) -> None:
        response = await client.post(
            self.request_password_reset_endpoint,
            json={"email": self.user_email},
        )

        assert response.status_code == 200

        stmt = select(func.count(select(PasswordResetTokenModel.id)))
        tokens_count = await db_session.scalar(stmt)

        assert tokens_count == 0

    async def test_successful_password_reset(
        self, client: AsyncClient, db_session: AsyncSession
    ) -> None:
        user = await self._create_default_user(db_session)

        token = PasswordResetTokenModel(
            user_id=user.id,
        )

        db_session.add(token)
        await db_session.commit()
        await db_session.refresh(token)

        response = await client.post(
            self.reset_password_complete_endpoint,
            json={
                "email": self.user_email,
                "token": token.token,
                "password": self.user_new_password,
            },
        )

        assert response.status_code == 200

        await db_session.refresh(user)

        assert user.verify_password(self.user_new_password)

    async def test_password_reset_with_invalid_token(
        self, client: AsyncClient, db_session: AsyncSession
    ) -> None:
        user = await self._create_default_user(db_session)

        token = PasswordResetTokenModel(
            user_id=user.id,
        )

        db_session.add(token)
        await db_session.commit()
        await db_session.refresh(token)

        response = await client.post(
            self.reset_password_complete_endpoint,
            json={
                "email": self.user_email,
                "token": "invalid_token",
                "password": self.user_new_password,
            },
        )

        assert response.status_code == 400

        await db_session.refresh(user)

        assert not user.verify_password(self.user_new_password)

    async def test_password_reset_with_invalid_email(
        self, client: AsyncClient, db_session: AsyncSession
    ) -> None:
        user = await self._create_default_user(db_session)

        token = PasswordResetTokenModel(
            user_id=user.id,
        )

        db_session.add(token)
        await db_session.commit()
        await db_session.refresh(token)

        response = await client.post(
            self.reset_password_complete_endpoint,
            json={
                "email": "invalidemail@example.com",
                "token": token.token,
                "password": self.user_new_password,
            },
        )

        assert response.status_code == 400

        await db_session.refresh(user)

        assert not user.verify_password(self.user_new_password)

    async def test_password_reset_with_expired_token(
        self, client: AsyncClient, db_session: AsyncSession
    ) -> None:
        user = await self._create_default_user(db_session)

        token = PasswordResetTokenModel(
            user_id=user.id,
        )

        token.expires_at = datetime.now(timezone.utc) - timedelta(hours=9999)

        db_session.add(token)
        await db_session.commit()
        await db_session.refresh(token)

        response = await client.post(
            self.reset_password_complete_endpoint,
            json={
                "email": self.user_email,
                "token": token.token,
                "password": self.user_new_password,
            },
        )

        assert response.status_code == 400

        await db_session.refresh(user)

        assert not user.verify_password(self.user_new_password)


class TestPasswordChangeEndpoint:
    password_change_endpoint = "/api/v1/accounts/password/change"

    user_email = "user@example.com"
    user_password = "1Qazcde3"
    user_new_password = "1NewPassword2"

    @pytest.fixture
    async def default_user(self, db_session: AsyncSession) -> UserModel:
        group = await _get_default_user_group(db_session)

        user = UserModel.create(
            email=self.user_email, raw_password=self.user_password, group_id=group.id
        )

        user.is_active = True

        db_session.add(user)
        await db_session.commit()
        await db_session.refresh(user)

        return user

    @pytest.fixture
    async def override_get_current_user_dependency(self, default_user):
        app.dependency_overrides[get_current_user] = lambda: default_user
        yield
        app.dependency_overrides.pop(get_current_user, None)

    async def test_successful_password_change(
        self,
        default_user,
        override_get_current_user_dependency,
        client: AsyncClient,
        db_session: AsyncSession,
    ) -> None:
        response = await client.post(
            self.password_change_endpoint,
            json={
                "old_password": self.user_password,
                "new_password": self.user_new_password,
            },
        )

        assert response.status_code == 200

        await db_session.refresh(default_user)

        assert default_user.verify_password(self.user_new_password)

    @pytest.mark.parametrize(
        "old_password,new_password",
        [
            ("incorrect_password", "1NewPassword2"),
            ("1Qazcde3", "1Qazcde3"),
        ],
    )
    async def test_unsuccessful_password_change(
        self,
        default_user,
        override_get_current_user_dependency,
        client: AsyncClient,
        db_session: AsyncSession,
        old_password: str,
        new_password: str,
    ) -> None:
        response = await client.post(
            self.password_change_endpoint,
            json={
                "old_password": old_password,
                "new_password": new_password,
            },
        )

        assert response.status_code == 400

        await db_session.refresh(default_user)

        assert not default_user.verify_password(self.user_new_password)

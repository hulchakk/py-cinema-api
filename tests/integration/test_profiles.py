from decimal import Decimal

from httpx import AsyncClient
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from database.models.movies import MovieModel
from database.models.orders import OrderModel
from database.models.payments import PaymentModel, PaymentStatusEnum, PaymentItemModel
from database.models.profiles import UserProfileModel, GenderEnum


class TestUserProfileEndpoints:
    user_profile_endpoint = "/api/v1/me"

    async def test_successful_get_user_profile(
        self,
        default_user,
        override_get_current_user_dependency,
        db_session: AsyncSession,
        client: AsyncClient,
    ) -> None:
        profile = UserProfileModel(
            user_id=default_user.id,
            first_name="John",
            last_name="Doe",
            gender=GenderEnum.MALE,
        )

        db_session.add(profile)
        await db_session.commit()

        response = await client.get(self.user_profile_endpoint)

        assert response.status_code == 200

        response_dict = response.json()

        assert response_dict["first_name"] == "John"
        assert response_dict["last_name"] == "Doe"
        assert response_dict["gender"] == GenderEnum.MALE

    async def test_unsuccessful_get_user_profile(
        self,
        default_user,
        override_get_current_user_dependency,
        db_session: AsyncSession,
        client: AsyncClient,
    ) -> None:
        response = await client.get(self.user_profile_endpoint)

        assert response.status_code == 404

    async def test_successful_create_user_profile(
        self,
        default_user,
        override_get_current_user_dependency,
        db_session: AsyncSession,
        client: AsyncClient,
    ) -> None:
        response = await client.post(
            self.user_profile_endpoint,
            json={
                "first_name": "John",
                "last_name": "Doe",
                "gender": GenderEnum.MALE,
            },
        )

        assert response.status_code == 201

        stmt = select(UserProfileModel).where(
            UserProfileModel.user_id == default_user.id
        )
        profile = await db_session.scalar(stmt)

        assert profile is not None
        assert profile.first_name == "John"
        assert profile.last_name == "Doe"
        assert profile.gender == GenderEnum.MALE

    async def test_create_user_profile_when_it_is_already_exists(
        self,
        default_user,
        override_get_current_user_dependency,
        db_session: AsyncSession,
        client: AsyncClient,
    ) -> None:
        profile = UserProfileModel(
            user_id=default_user.id,
            first_name="John",
            last_name="Doe",
            gender=GenderEnum.MALE,
        )

        db_session.add(profile)
        await db_session.commit()
        await db_session.refresh(profile)

        response = await client.post(
            self.user_profile_endpoint,
            json={
                "first_name": "New",
                "last_name": "Profile",
                "gender": GenderEnum.FEMALE,
            },
        )

        assert response.status_code == 409

        stmt = select(UserProfileModel).where(
            UserProfileModel.user_id == default_user.id
        )
        profile_after_response = await db_session.scalar(stmt)

        assert profile_after_response.first_name == profile.first_name
        assert profile_after_response.last_name == profile.last_name
        assert profile.gender == profile.gender

    async def test_create_user_profile_with_no_data(
        self,
        default_user,
        override_get_current_user_dependency,
        db_session: AsyncSession,
        client: AsyncClient,
    ) -> None:
        response = await client.post(
            self.user_profile_endpoint,
            json={},
        )

        assert response.status_code == 400

        stmt = select(UserProfileModel).where(
            UserProfileModel.user_id == default_user.id
        )
        profile = await db_session.scalar(stmt)

        assert profile is None


class TestLibraryEndpoint:
    library_endpoint = "/api/v1/me/library"

    async def test_get_user_library_empty(
        self,
        default_user,
        override_get_current_user_dependency,
        populate_movies,
        db_session: AsyncSession,
        client: AsyncClient,
    ) -> None:
        response = await client.get(self.library_endpoint)

        assert response.status_code == 404

    async def test_successful_get_user_library(
        self,
        default_user,
        override_get_current_user_dependency,
        populate_movies,
        db_session: AsyncSession,
        client: AsyncClient,
    ) -> None:
        order = OrderModel(
            user_id=default_user.id,
        )

        db_session.add(order)

        await db_session.flush()

        payment = PaymentModel(
            user_id=default_user.id,
            order_id=order.id,
            amount=Decimal(100),
            status=PaymentStatusEnum.SUCCESSFUL,
        )

        db_session.add(payment)

        await db_session.flush()

        stmt = select(MovieModel).limit(3)
        movies = (await db_session.scalars(stmt)).all()

        total = len(movies)

        for movie in movies:
            payment_item = PaymentItemModel(
                payment_id=payment.id,
                movie_id=movie.id,
                price_at_payment=Decimal(33.33),
            )

            db_session.add(payment_item)

        await db_session.commit()

        response = await client.get(self.library_endpoint)

        assert response.status_code == 200

        assert response.json()["total"] == total
        assert len(response.json()["results"]) == total

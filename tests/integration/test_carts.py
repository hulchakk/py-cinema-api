from decimal import Decimal

from httpx import AsyncClient
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import joinedload

from database.models.carts import CartModel, CartItemModel
from database.models.movies import MovieModel
from database.models.orders import OrderModel
from database.models.payments import PaymentModel, PaymentStatusEnum, PaymentItemModel


class TestCart:
    cart_endpoint = "/api/v1/cart"
    cart_item_endpoint = "/api/v1/cart/items"

    async def test_successful_get_user_cart(
        self,
        default_user,
        override_get_current_user_dependency,
        populate_movies,
        db_session: AsyncSession,
        client: AsyncClient,
    ) -> None:
        stmt = select(MovieModel).limit(3)
        movies = (await db_session.scalars(stmt)).all()

        cart = CartModel(
            user_id=default_user.id,
        )

        db_session.add(cart)
        await db_session.flush()

        for movie in movies:
            cart_item = CartItemModel(
                cart_id=cart.id,
                movie_id=movie.id,
            )
            db_session.add(cart_item)

        await db_session.commit()

        response = await client.get(
            self.cart_endpoint,
        )

        assert response.status_code == 200

        items = response.json()["items"]

        assert len(items) == len(movies)

    async def test_successful_add_item_to_cart(
        self,
        default_user,
        override_get_current_user_dependency,
        populate_movies,
        db_session: AsyncSession,
        client: AsyncClient,
    ) -> None:
        stmt = select(MovieModel).limit(1)
        movie = await db_session.scalar(stmt)

        response = await client.post(
            self.cart_item_endpoint,
            json={
                "movie_id": movie.id,
            },
        )

        assert response.status_code == 201

        stmt = (
            select(CartModel)
            .where(CartModel.user_id == default_user.id)
            .options(joinedload(CartModel.items))
        )
        cart = await db_session.scalar(stmt)

        assert cart is not None
        assert len(cart.items) == 1

        assert cart.items[0].movie_id == movie.id

    async def test_add_unexisting_movie_to_cart(
        self,
        default_user,
        override_get_current_user_dependency,
        db_session: AsyncSession,
        client: AsyncClient,
    ) -> None:
        response = await client.post(
            self.cart_item_endpoint,
            json={
                "movie_id": 99999,
            },
        )

        assert response.status_code == 404

        stmt = (
            select(CartModel)
            .where(CartModel.user_id == default_user.id)
            .options(joinedload(CartModel.items))
        )
        cart = await db_session.scalar(stmt)

        assert cart is None

    async def test_add_movie_to_cart_twice(
        self,
        default_user,
        override_get_current_user_dependency,
        populate_movies,
        db_session: AsyncSession,
        client: AsyncClient,
    ) -> None:
        stmt = select(MovieModel).limit(1)
        movie = await db_session.scalar(stmt)

        cart = CartModel(
            user_id=default_user.id,
        )

        db_session.add(cart)
        await db_session.flush()

        cart_item = CartItemModel(
            cart_id=cart.id,
            movie_id=movie.id,
        )

        db_session.add(cart_item)
        await db_session.commit()

        response = await client.post(
            self.cart_item_endpoint,
            json={
                "movie_id": movie.id,
            },
        )

        assert response.status_code == 400

        stmt = (
            select(CartModel)
            .where(CartModel.user_id == default_user.id)
            .options(joinedload(CartModel.items))
        )
        cart = await db_session.scalar(stmt)

        assert cart is not None
        assert len(cart.items) == 1

    async def test_add_item_to_cart_when_already_purchased(
        self,
        default_user,
        override_get_current_user_dependency,
        populate_movies,
        db_session: AsyncSession,
        client,
    ) -> None:
        stmt = select(MovieModel).limit(1)
        movie = await db_session.scalar(stmt)

        order = OrderModel(
            user_id=default_user.id,
        )

        db_session.add(order)
        await db_session.flush()

        payment = PaymentModel(
            user_id=default_user.id,
            order_id=order.id,
            amount=Decimal("100"),
            status=PaymentStatusEnum.SUCCESSFUL,
        )
        db_session.add(payment)
        await db_session.flush()

        payment_item = PaymentItemModel(
            payment_id=payment.id,
            movie_id=movie.id,
            price_at_payment=Decimal("100"),
        )

        db_session.add(payment_item)
        await db_session.commit()

        response = await client.post(
            self.cart_item_endpoint,
            json={
                "movie_id": movie.id,
            },
        )

        assert response.status_code == 400

        stmt = select(CartModel).where(CartModel.user_id == default_user.id)
        cart = await db_session.scalar(stmt)

        assert cart is None

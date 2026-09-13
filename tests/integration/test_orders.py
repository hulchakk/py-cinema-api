from decimal import Decimal

from httpx import AsyncClient
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import joinedload

from database.models.carts import CartModel, CartItemModel
from database.models.movies import MovieModel
from database.models.orders import OrderModel, OrderStatusEnum, OrderItemModel
from database.models.payments import PaymentModel, PaymentStatusEnum, PaymentItemModel


class TestOrderCreation:
    order_create_endpoint = "/api/v1/orders"

    async def test_successful_create_order(
        self,
        populate_movies,
        default_user,
        override_get_current_user_dependency,
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

        response = await client.post(
            self.order_create_endpoint,
        )

        assert response.status_code == 201

        stmt = (
            select(OrderModel)
            .where(OrderModel.user_id == default_user.id)
            .options(
                joinedload(OrderModel.items),
            )
        )
        order = await db_session.scalar(stmt)

        assert order is not None
        assert len(order.items) == len(movies)

    async def test_create_order_without_cart(
        self,
        default_user,
        override_get_current_user_dependency,
        db_session: AsyncSession,
        client: AsyncClient,
    ) -> None:
        response = await client.post(
            self.order_create_endpoint,
        )

        assert response.status_code == 404

        stmt = select(OrderModel).where(OrderModel.user_id == default_user.id)
        order = await db_session.scalar(stmt)

        assert order is None

    async def test_create_order_with_purchased_movie(
        self,
        populate_movies,
        default_user,
        override_get_current_user_dependency,
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

        order = OrderModel(
            user_id=default_user.id,
            status=OrderStatusEnum.PAID,
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

        payment_item = PaymentItemModel(
            payment_id=payment.id,
            movie_id=movies[0].id,
            price_at_payment=Decimal(100),
        )

        db_session.add(payment_item)

        await db_session.commit()

        response = await client.post(
            self.order_create_endpoint,
        )

        assert response.status_code == 400

        stmt = select(OrderModel).where(
            OrderModel.user_id == default_user.id,
            OrderModel.status == OrderStatusEnum.PENDING,
        )
        order = await db_session.scalar(stmt)

        assert order is None

    async def test_create_order_with_movie_in_other_order(
        self,
        populate_movies,
        default_user,
        override_get_current_user_dependency,
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

        await db_session.flush()

        order = OrderModel(
            user_id=default_user.id,
            status=OrderStatusEnum.PENDING,
        )

        db_session.add(order)
        await db_session.flush()

        order_item = OrderItemModel(
            order_id=order.id,
            movie_id=movies[0].id,
            price_at_order=Decimal(100),
        )

        db_session.add(order_item)
        await db_session.commit()

        response = await client.post(
            self.order_create_endpoint,
        )

        assert response.status_code == 400

        stmt = select(OrderModel).where(OrderModel.user_id == default_user.id)
        orders = (await db_session.scalars(stmt)).all()

        assert len(orders) == 1

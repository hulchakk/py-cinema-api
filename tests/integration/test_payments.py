import json
from decimal import Decimal

import pytest
from httpx import AsyncClient
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import joinedload

from database.models.movies import MovieModel
from database.models.orders import OrderModel, OrderStatusEnum, OrderItemModel
from database.models.payments import PaymentModel, PaymentStatusEnum


class TestStripeWebhookEndpoint:
    webhook_endpoint = "/api/v1/payments/webhook"

    @pytest.fixture(autouse=True)
    def mock_stripe_webhook(self, monkeypatch):
        def mock_construct_event(payload, sig_header, secret):
            if isinstance(payload, bytes):
                payload = payload.decode("utf-8")
            return json.loads(payload)

        monkeypatch.setattr("stripe.Webhook.construct_event", mock_construct_event)

    @pytest.fixture
    async def order_id(
        self,
        populate_movies,
        default_user,
        db_session,
    ) -> int:
        order = OrderModel(
            user_id=default_user.id,
            status=OrderStatusEnum.PENDING,
        )

        db_session.add(order)
        await db_session.flush()

        stmt = select(MovieModel).limit(3)
        movies = (await db_session.scalars(stmt)).all()

        for movie in movies:
            order_item = OrderItemModel(
                order_id=order.id,
                movie_id=movie.id,
                price_at_order=Decimal(1),
            )
            db_session.add(order_item)

        await db_session.commit()

        return order.id

    async def test_successful_stripe_webhook(
        self,
        order_id,
        db_session: AsyncSession,
        client: AsyncClient,
    ) -> None:
        event_payload = {
            "type": "checkout.session.completed",
            "data": {
                "object": {
                    "metadata": {"order_id": str(order_id)},
                    "payment_intent": "pi_test_987654",
                    "currency": "usd",
                }
            },
        }

        response = await client.post(
            self.webhook_endpoint,
            json=event_payload,
            headers={"stripe-signature": "any_dummy_signature"},
        )

        assert response.status_code == 200

        stmt = (
            select(PaymentModel)
            .where(PaymentModel.order_id == order_id)
            .options(joinedload(PaymentModel.items))
        )
        payment = await db_session.scalar(stmt)

        stmt = select(MovieModel).limit(3)
        movies_count = len((await db_session.scalars(stmt)).all())

        assert payment is not None
        assert payment.status == PaymentStatusEnum.SUCCESSFUL
        assert len(payment.items) == movies_count

    async def test_stripe_webhook_unexisting_order_payment(
        self,
        db_session,
        client: AsyncClient,
    ) -> None:
        unexisting_order_id = 999999

        event_payload = {
            "type": "checkout.session.completed",
            "data": {
                "object": {
                    "metadata": {"order_id": str(unexisting_order_id)},
                    "payment_intent": "pi_test_987654",
                    "currency": "usd",
                }
            },
        }

        response = await client.post(
            self.webhook_endpoint,
            json=event_payload,
            headers={"stripe-signature": "any_dummy_signature"},
        )

        assert response.status_code == 404

        stmt = select(PaymentModel).where(PaymentModel.order_id == unexisting_order_id)
        payment = await db_session.scalar(stmt)

        assert payment is None

    async def test_unsuccessful_payment_stripe_webhook(
        self,
        order_id,
        db_session,
        client: AsyncClient,
    ) -> None:
        event_payload = {
            "type": "checkout.session.canceled",
            "data": {
                "object": {
                    "metadata": {"order_id": order_id},
                    "payment_intent": "pi_test_987654",
                    "currency": "usd",
                }
            },
        }

        response = await client.post(
            self.webhook_endpoint,
            json=event_payload,
            headers={"stripe-signature": "any_dummy_signature"},
        )

        assert response.status_code == 200

        stmt = select(PaymentModel).where(PaymentModel.order_id == order_id)
        payment = await db_session.scalar(stmt)

        assert payment is None

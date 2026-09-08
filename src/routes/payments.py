import stripe
from fastapi import APIRouter, Header, HTTPException, Depends, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload
from starlette.requests import Request

from config.settings import settings
from database.models.orders import OrderModel, OrderStatusEnum
from database.models.payments import PaymentModel, PaymentStatusEnum, PaymentItemModel
from database.session import get_db

router = APIRouter(
    prefix="/payments",
)


@router.post("/webhook")
async def stripe_webhook(
    request: Request,
    stripe_signature: str = Header(..., alias="stripe-signature"),
    db: AsyncSession = Depends(get_db),
):
    payload = await request.body()

    try:
        event = stripe.Webhook.construct_event(
            payload, stripe_signature, settings.STRIPE_WEBHOOK_SECRET
        )
    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid payload"
        )
    except stripe.error.SignatureVerificationError:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid signature"
        )

    if event["type"] == "checkout.session.completed":
        session = event["data"]["object"]

        order_id = int(session["metadata"]["order_id"])
        external_payment_id = session["payment_intent"]

        existing_payment = await db.scalar(
            select(PaymentModel).where(
                PaymentModel.external_payment_id == external_payment_id
            )
        )
        if existing_payment:
            return {"status": "already_processed"}

        stmt = (
            select(OrderModel)
            .where(OrderModel.id == order_id)
            .options(selectinload(OrderModel.items))
        )
        order = await db.scalar(stmt)

        if not order:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND, detail="Order not found"
            )

        order.status = OrderStatusEnum.PAID

        payment = PaymentModel(
            user_id=order.user_id,
            order_id=order_id,
            external_payment_id=external_payment_id,
            amount=order.total_amount,
            status=PaymentStatusEnum.SUCCESSFUL,
        )

        db.add(payment)

        await db.flush()

        for item in order.items:
            payment_item = PaymentItemModel(
                payment_id=payment.id,
                movie_id=item.movie_id,
                price_at_payment=item.price_at_order,
            )
            db.add(payment_item)

        await db.commit()

    return {"status": "success"}

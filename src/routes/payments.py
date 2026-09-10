import stripe
from fastapi import APIRouter, Header, HTTPException, Depends, status, BackgroundTasks
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload
from starlette.requests import Request

from config.dependencies import get_accounts_email_notificator
from config.settings import settings
from database.models.accounts import UserModel
from database.models.orders import OrderModel, OrderStatusEnum
from database.models.payments import PaymentModel, PaymentStatusEnum, PaymentItemModel
from database.session import get_db
from routes.dependencies import PaginationParams
from schemas.pagination import PaginatedResponseSchema
from schemas.payments import PaymentListResponseSchema, PaymentRetrieveResponseSchema
from security.dependencies import get_current_user
from services.notifications.interfaces import EmailSenderInterface
from utils.paginator import paginate_response

router = APIRouter(
    prefix="/payments",
)


@router.get(
    "",
    status_code=status.HTTP_200_OK,
    response_model=PaginatedResponseSchema[PaymentListResponseSchema],
)
async def get_user_payments(
    request: Request,
    pagination: PaginationParams = Depends(),
    user: UserModel = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    stmt = select(func.count(PaymentModel.id)).where(PaymentModel.user_id == user.id)
    total = await db.scalar(stmt) or 0

    if total == 0:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Payments not found."
        )

    stmt = (
        select(PaymentModel)
        .where(PaymentModel.user_id == user.id)
        .offset(pagination.offset)
        .limit(pagination.limit)
    )

    results = list((await db.scalars(stmt)).all()) or []

    return paginate_response(
        request=request, results=results, total=total, pagination=pagination
    )


@router.get(
    "/{payment_id}",
    status_code=status.HTTP_200_OK,
    response_model=PaymentRetrieveResponseSchema,
)
async def get_payment_details(
    payment_id: int,
    user: UserModel = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    stmt = (
        select(PaymentModel)
        .where(PaymentModel.id == payment_id, PaymentModel.user_id == user.id)
        .options(selectinload(PaymentModel.items).joinedload(PaymentItemModel.movie))
    )
    payment = await db.scalar(stmt)

    if not payment:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Payment not found."
        )

    return payment


@router.post("/webhook")
async def stripe_webhook(
    request: Request,
    background_tasks: BackgroundTasks,
    stripe_signature: str = Header(..., alias="stripe-signature"),
    db: AsyncSession = Depends(get_db),
    email_sender: EmailSenderInterface = Depends(get_accounts_email_notificator),
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
            .options(
                selectinload(OrderModel.items),
                selectinload(OrderModel.user),
            )
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

        background_tasks.add_task(
            email_sender.send_payment_receipt_email,
            email=order.user.email,
            payment_id=str(payment.id),
            amount=float(payment.amount),
            currency=session.get("currency", "usd").upper(),
        )

    return {"status": "success"}

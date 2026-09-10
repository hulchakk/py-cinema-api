import stripe
from fastapi import (
    APIRouter,
    Header,
    HTTPException,
    Depends,
    status,
    BackgroundTasks,
    Path,
)
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
    summary="Get user payments",
    description="Retrieves a paginated list of all payment transactions belonging to the currently authenticated user.",
    responses={
        status.HTTP_200_OK: {
            "description": "Paginated list of payments retrieved successfully.",
        },
        status.HTTP_401_UNAUTHORIZED: {
            "description": "Authentication token missing or invalid.",
        },
        status.HTTP_404_NOT_FOUND: {
            "description": "No payments found for the current user.",
            "content": {
                "application/json": {"example": {"detail": "Payments not found."}}
            },
        },
    },
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
    summary="Get payment details",
    description="Retrieves detailed information about a specific payment transaction belonging to the current user, including payment items and associated movie details.",
    responses={
        status.HTTP_200_OK: {
            "model": PaymentRetrieveResponseSchema,
            "description": "Payment details retrieved successfully.",
        },
        status.HTTP_401_UNAUTHORIZED: {
            "description": "Authentication token missing or invalid.",
        },
        status.HTTP_404_NOT_FOUND: {
            "description": "Payment not found or does not belong to the user.",
            "content": {
                "application/json": {"example": {"detail": "Payment not found."}}
            },
        },
    },
)
async def get_payment_details(
    payment_id: int = Path(
        ...,
        title="Payment ID",
        description="The ID of the payment to retrieve.",
        example=1,
    ),
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


@router.post(
    "/webhook",
    status_code=status.HTTP_200_OK,
    summary="Stripe Webhook Listener",
    description="Handles webhook events sent by Stripe. Processes successful checkout sessions (`checkout.session.completed`), creates payment records with payment items, updates order status to PAID, and queues payment receipt emails.",
    responses={
        status.HTTP_200_OK: {
            "description": "Event processed or acknowledged.",
            "content": {
                "application/json": {
                    "examples": {
                        "processed": {"value": {"status": "success"}},
                        "already_processed": {"value": {"status": "already_processed"}},
                    }
                }
            },
        },
        status.HTTP_400_BAD_REQUEST: {
            "description": "Invalid payload or signature verification failed.",
            "content": {
                "application/json": {
                    "examples": {
                        "invalid_payload": {"value": {"detail": "Invalid payload"}},
                        "invalid_signature": {"value": {"detail": "Invalid signature"}},
                    }
                }
            },
        },
        status.HTTP_404_NOT_FOUND: {
            "description": "Order associated with payment metadata not found.",
            "content": {"application/json": {"example": {"detail": "Order not found"}}},
        },
    },
)
async def stripe_webhook(
    request: Request,
    background_tasks: BackgroundTasks,
    stripe_signature: str = Header(
        ...,
        alias="stripe-signature",
        title="Stripe Signature",
        description="Signature provided in the headers by Stripe to verify webhook integrity.",
    ),
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

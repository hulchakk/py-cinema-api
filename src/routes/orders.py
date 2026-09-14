from decimal import Decimal

from fastapi import Depends, APIRouter, HTTPException, BackgroundTasks, Path
from sqlalchemy import select, func, exists, and_
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload
from starlette import status
from starlette.requests import Request

from config.dependencies import get_accounts_email_notificator
from database.models.accounts import UserModel
from database.models.carts import CartModel, CartItemModel
from database.models.orders import OrderModel, OrderItemModel, OrderStatusEnum
from database.models.payments import PaymentItemModel, PaymentModel, PaymentStatusEnum
from database.session import get_db
from routes.dependencies import PaginationParams
from schemas.accounts import MessageResponseSchema
from schemas.orders import (
    OrderListResponseSchema,
    OrderRetrieveResponseSchema,
    CreateCheckoutSessionResponseSchema,
    CreateCheckoutSessionRequestSchema,
)
from schemas.pagination import PaginatedResponseSchema
from security.dependencies import get_current_user
from services.notifications.interfaces import EmailSenderInterface
from services.payments.interfaces import PaymentInterface
from services.payments.stripe import StripePaymentService
from utils.paginator import paginate_response

router = APIRouter(
    prefix="/orders",
)


@router.post(
    "",
    status_code=status.HTTP_201_CREATED,
    response_model=MessageResponseSchema,
    summary="Create a new order",
    description="Creates a new pending order from the current user's shopping cart. Validates that the cart is not empty, movies have not been previously purchased, and there are no conflicting pending orders with the same movies. Clears the cart and queues an order confirmation email upon success.",
    responses={
        status.HTTP_201_CREATED: {
            "model": MessageResponseSchema,
            "description": "Order successfully created.",
            "content": {
                "application/json": {
                    "examples": {
                        "success": {"value": {"message": "Successfully created order"}}
                    }
                }
            },
        },
        status.HTTP_400_BAD_REQUEST: {
            "description": "Cart contains already purchased movies or movies present in another pending order.",
            "content": {
                "application/json": {
                    "examples": {
                        "already_purchased": {
                            "value": {
                                "detail": "Your cart contains movies that you have already purchased."
                            }
                        },
                        "pending_conflict": {
                            "value": {
                                "detail": "You already have a pending order containing one or more of these movies."
                            }
                        },
                    }
                }
            },
        },
        status.HTTP_401_UNAUTHORIZED: {
            "description": "Authentication token missing or invalid.",
        },
        status.HTTP_404_NOT_FOUND: {
            "description": "Cart is empty or does not exist for the user.",
            "content": {
                "application/json": {
                    "examples": {
                        "cart_not_found": {"value": {"detail": "Cart not found."}}
                    }
                }
            },
        },
    },
)
async def create_order(
    background_tasks: BackgroundTasks,
    user: UserModel = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
    email_sender: EmailSenderInterface = Depends(get_accounts_email_notificator),
):
    stmt = (
        select(CartModel)
        .where(CartModel.user_id == user.id)
        .options(selectinload(CartModel.items).joinedload(CartItemModel.movie))
    )
    cart = await db.scalar(stmt)

    if not cart or len(cart.items) == 0:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Cart not found."
        )

    cart_movie_ids = [item.movie_id for item in cart.items]

    purchased_stmt = select(
        exists().where(
            PaymentItemModel.movie_id.in_(cart_movie_ids),
            PaymentItemModel.payment.has(
                and_(
                    PaymentModel.user_id == user.id,
                    PaymentModel.status == PaymentStatusEnum.SUCCESSFUL,
                )
            ),
        )
    )
    has_purchased_movies = await db.scalar(purchased_stmt)

    if has_purchased_movies:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Your cart contains movies that you have already purchased.",
        )

    pending_order_stmt = select(
        exists().where(
            OrderItemModel.movie_id.in_(cart_movie_ids),
            OrderItemModel.order.has(
                and_(
                    OrderModel.user_id == user.id,
                    OrderModel.status == OrderStatusEnum.PENDING,
                )
            ),
        )
    )
    has_pending_conflict = await db.scalar(pending_order_stmt)

    if has_pending_conflict:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="You already have a pending order containing one or more of these movies.",
        )

    order = OrderModel(
        user_id=user.id,
        status=OrderStatusEnum.PENDING,
    )

    db.add(order)
    await db.flush()

    total_amount = Decimal("0.00")
    order_items_data = []

    for cart_item in cart.items:
        current_price = Decimal(str(cart_item.movie.price))

        order_item = OrderItemModel(
            order_id=order.id,
            movie_id=cart_item.movie_id,
            price_at_order=current_price,
        )

        db.add(order_item)
        total_amount += current_price
        order_items_data.append(
            {"title": cart_item.movie.name, "price": float(current_price)}
        )

    order.total_amount = total_amount

    await db.delete(cart)
    await db.commit()

    order_details = {
        "items": order_items_data,
        "total_amount": float(total_amount),
    }

    background_tasks.add_task(
        email_sender.send_order_confirmation_email,
        email=user.email,
        order_id=str(order.id),
        order_details=order_details,
    )

    return MessageResponseSchema(
        message="Successfully created order",
    )


@router.get(
    "",
    status_code=status.HTTP_200_OK,
    response_model=PaginatedResponseSchema[OrderListResponseSchema],
    summary="Get user orders",
    description="Retrieves a paginated list of all orders belonging to the authenticated user.",
    responses={
        status.HTTP_200_OK: {
            "description": "Paginated list of user orders retrieved successfully.",
        },
        status.HTTP_401_UNAUTHORIZED: {
            "description": "Authentication token missing or invalid.",
        },
        status.HTTP_404_NOT_FOUND: {
            "description": "No orders found for the user.",
            "content": {
                "application/json": {
                    "examples": {
                        "orders_not_found": {"value": {"detail": "Orders not found."}}
                    }
                }
            },
        },
    },
)
async def get_user_orders(
    request: Request,
    pagination: PaginationParams = Depends(),
    user: UserModel = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    stmt = select(func.count(OrderModel.id)).where(OrderModel.user_id == user.id)
    total = await db.scalar(stmt) or 0

    if total == 0:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Orders not found."
        )

    stmt = (
        select(OrderModel)
        .where(OrderModel.user_id == user.id)
        .offset(pagination.offset)
        .limit(pagination.limit)
    )

    results = list((await db.scalars(stmt)).all()) or []

    return paginate_response(
        request=request, results=results, total=total, pagination=pagination
    )


@router.get(
    "/{order_id}",
    status_code=status.HTTP_200_OK,
    response_model=OrderRetrieveResponseSchema,
    summary="Get order details",
    description="Retrieves detailed information about a specific order belonging to the current user, including order items and associated movie details.",
    responses={
        status.HTTP_200_OK: {
            "model": OrderRetrieveResponseSchema,
            "description": "Order details retrieved successfully.",
        },
        status.HTTP_401_UNAUTHORIZED: {
            "description": "Authentication token missing or invalid.",
        },
        status.HTTP_404_NOT_FOUND: {
            "description": "Order not found or does not belong to the user.",
            "content": {
                "application/json": {
                    "examples": {
                        "order_not_found": {"value": {"detail": "Order not found."}}
                    }
                }
            },
        },
    },
)
async def get_order_details(
    order_id: int = Path(
        ...,
        title="Order ID",
        description="The ID of the order to retrieve.",
        examples=[1],
    ),
    user: UserModel = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    stmt = (
        select(OrderModel)
        .where(OrderModel.id == order_id, OrderModel.user_id == user.id)
        .options(selectinload(OrderModel.items).joinedload(OrderItemModel.movie))
    )
    order = await db.scalar(stmt)

    if not order:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Order not found."
        )

    return order


@router.delete(
    "/{order_id}",
    status_code=status.HTTP_200_OK,
    response_model=MessageResponseSchema,
    summary="Cancel order",
    description="Cancels an existing pending order belonging to the user. Orders that are not in PENDING status cannot be canceled.",
    responses={
        status.HTTP_200_OK: {
            "model": MessageResponseSchema,
            "description": "Order successfully canceled.",
            "content": {
                "application/json": {
                    "examples": {
                        "success": {
                            "value": {"message": "Successfully canceled order."}
                        }
                    }
                }
            },
        },
        status.HTTP_400_BAD_REQUEST: {
            "description": "Order is not in PENDING status.",
            "content": {
                "application/json": {
                    "examples": {
                        "not_pending": {
                            "value": {
                                "detail": "Cannot cancel order with status 'successful'. Only pending orders can be canceled."
                            }
                        }
                    }
                }
            },
        },
        status.HTTP_401_UNAUTHORIZED: {
            "description": "Authentication token missing or invalid.",
        },
        status.HTTP_404_NOT_FOUND: {
            "description": "Order not found or does not belong to the user.",
            "content": {
                "application/json": {
                    "examples": {
                        "order_not_found": {"value": {"detail": "Order not found."}}
                    }
                }
            },
        },
    },
)
async def cancel_order(
    order_id: int = Path(
        ...,
        title="Order ID",
        description="The ID of the order to cancel.",
        examples=[1],
    ),
    user: UserModel = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    stmt = select(OrderModel).where(
        OrderModel.id == order_id,
        OrderModel.user_id == user.id,
    )
    order = await db.scalar(stmt)

    if not order:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Order not found."
        )

    if order.status != OrderStatusEnum.PENDING:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Cannot cancel order with status '{order.status.value}'. Only pending orders can be canceled.",
        )

    order.status = OrderStatusEnum.CANCELED

    await db.commit()

    return MessageResponseSchema(
        message="Successfully canceled order.",
    )


@router.post(
    "/{order_id}/pay",
    status_code=status.HTTP_200_OK,
    response_model=CreateCheckoutSessionResponseSchema,
    summary="Create payment checkout session",
    description="Generates a payment checkout session URL (e.g. Stripe) for a pending order. Requires valid success and cancel redirect URLs.",
    responses={
        status.HTTP_200_OK: {
            "model": CreateCheckoutSessionResponseSchema,
            "description": "Checkout session created successfully.",
            "content": {
                "application/json": {
                    "examples": {
                        "checkout_session": {
                            "value": {
                                "checkout_url": "https://checkout.stripe.com/c/pay/cs_test_12345"
                            }
                        }
                    }
                }
            },
        },
        status.HTTP_400_BAD_REQUEST: {
            "description": "Order is not in PENDING status and cannot be paid.",
            "content": {
                "application/json": {
                    "examples": {
                        "already_paid": {
                            "value": {
                                "detail": "Order 1 cannot be paid because it is already successful."
                            }
                        }
                    }
                }
            },
        },
        status.HTTP_401_UNAUTHORIZED: {
            "description": "Authentication token missing or invalid.",
        },
        status.HTTP_404_NOT_FOUND: {
            "description": "Order not found or does not belong to the user.",
            "content": {
                "application/json": {
                    "examples": {
                        "order_not_found": {"value": {"detail": "Order not found."}}
                    }
                }
            },
        },
    },
)
async def create_checkout_session(
    data: CreateCheckoutSessionRequestSchema,
    order_id: int = Path(
        ...,
        title="Order ID",
        description="The ID of the order to pay for.",
        examples=[1],
    ),
    payment_service: PaymentInterface = Depends(StripePaymentService),
    user: UserModel = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    stmt = select(OrderModel).where(
        OrderModel.id == order_id, OrderModel.user_id == user.id
    )

    order = await db.scalar(stmt)

    if not order:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Order not found."
        )

    if order.status != OrderStatusEnum.PENDING:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Order {order.id} cannot be paid because it is already {order.status.value.lower()}.",
        )

    checkout_url = await payment_service.create_checkout_session(
        order_id=order_id,
        total_amount=order.total_amount,
        success_url=str(data.success_url),
        cancel_url=str(data.cancel_url),
    )

    return CreateCheckoutSessionResponseSchema(
        checkout_url=checkout_url,
    )

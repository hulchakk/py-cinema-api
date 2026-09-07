from decimal import Decimal

from fastapi import Depends, APIRouter, HTTPException
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload
from starlette import status
from starlette.requests import Request

from database.models.accounts import UserModel
from database.models.carts import CartModel, CartItemModel
from database.models.orders import OrderModel, OrderItemModel, OrderStatusEnum
from database.session import get_db
from routes.dependencies import PaginationParams
from schemas.accounts import MessageResponseSchema
from schemas.orders import OrderListResponseSchema, OrderRetrieveResponseSchema
from schemas.pagination import PaginatedResponseSchema
from security.dependencies import get_current_user

router = APIRouter(
    prefix="/orders",
)


@router.post(
    "",
    status_code=status.HTTP_201_CREATED,
    response_model=MessageResponseSchema,
)
async def create_order(
    user: UserModel = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    stmt = (
        select(CartModel)
        .where(CartModel.user_id == user.id)
        .options(selectinload(CartModel.items).joinedload(CartItemModel.movie))
    )
    cart = await db.scalar(stmt)

    if not cart or len(cart.items) == 0:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Cart not found"
        )

    order = OrderModel(
        user_id=user.id,
    )

    db.add(order)
    await db.flush()

    total_amount = Decimal("0.0")

    for cart_item in cart.items:
        order_item = OrderItemModel(
            order_id=order.id,
            movie_id=cart_item.movie_id,
            price_at_order=cart_item.movie.price,
        )

        db.add(order_item)
        total_amount += cart_item.movie.price

    order.total_amount = total_amount

    await db.delete(cart)
    await db.commit()

    return MessageResponseSchema(
        message="Successfully created order",
    )


@router.get(
    "",
    status_code=status.HTTP_200_OK,
    response_model=PaginatedResponseSchema[OrderListResponseSchema],
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

    has_next = (pagination.page * pagination.per_page) < total
    has_prev = pagination.page > 1

    next_page = None
    if has_next:
        next_page = str(
            request.url.include_query_params(
                page=pagination.page + 1,
                per_page=pagination.per_page,
            )
        )

    previous_page = None
    if has_prev:
        previous_page = str(
            request.url.include_query_params(
                page=pagination.page - 1,
                per_page=pagination.per_page,
            )
        )

    return PaginatedResponseSchema(
        results=results,
        total=total,
        per_page=pagination.per_page,
        page=pagination.page,
        previous_page=previous_page,
        next_page=next_page,
    )


@router.get(
    "/{order_id}",
    status_code=status.HTTP_200_OK,
    response_model=OrderRetrieveResponseSchema,
)
async def get_order_details(
    order_id: int,
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
)
async def cancel_order(
    order_id: int,
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

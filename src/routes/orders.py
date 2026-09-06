from decimal import Decimal

from fastapi import Depends, APIRouter, HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload
from starlette import status

from database.models.accounts import UserModel
from database.models.carts import CartModel, CartItemModel
from database.models.orders import OrderModel, OrderItemModel
from database.session import get_db
from schemas.accounts import MessageResponseSchema
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

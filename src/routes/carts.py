from fastapi import Depends, HTTPException, APIRouter
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from database.models.accounts import UserModel
from database.models.carts import CartModel
from database.session import get_db
from schemas.carts import CartResponseSchema
from security.dependencies import get_current_user

router = APIRouter(
    prefix="/cart",
)


@router.get("", response_model=CartResponseSchema)
async def get_user_cart(
    user: UserModel = Depends(get_current_user), db: AsyncSession = Depends(get_db)
):
    stmt = (
        select(CartModel)
        .where(CartModel.user_id == user.id)
        .options(
            selectinload(CartModel.items),
        )
    )
    cart = await db.scalar(stmt) or None

    if not cart:
        raise HTTPException(status_code=404, detail="Cart not found")

    return cart

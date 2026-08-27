from fastapi import Depends, HTTPException, APIRouter
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload, joinedload
from starlette import status

from database.models.accounts import UserModel
from database.models.carts import CartModel, CartItemModel
from database.models.movies import MovieModel
from database.session import get_db
from schemas.accounts import MessageResponseSchema
from schemas.carts import CartResponseSchema
from security.dependencies import get_current_user

router = APIRouter(
    prefix="/cart",
)


@router.get("", status_code=status.HTTP_200_OK, response_model=CartResponseSchema)
async def get_user_cart(
    user: UserModel = Depends(get_current_user), db: AsyncSession = Depends(get_db)
):
    stmt = (
        select(CartModel)
        .where(CartModel.user_id == user.id)
        .options(
            selectinload(CartModel.items)
            .joinedload(CartItemModel.movie)
            .options(
                selectinload(MovieModel.genres), joinedload(MovieModel.certification)
            ),
        )
    )
    cart = await db.scalar(stmt) or None

    if not cart:
        raise HTTPException(status_code=404, detail="Cart not found")

    return cart


@router.post(
    "/items", status_code=status.HTTP_201_CREATED, response_model=MessageResponseSchema
)
async def add_item_to_cart(
    movie_id: int,
    user: UserModel = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    movie = await db.get(MovieModel, movie_id)

    if not movie:
        raise HTTPException(status_code=404, detail="Movie not found")

    stmt = (
        select(CartModel)
        .where(CartModel.user_id == user.id)
        .options(selectinload(CartModel.items).joinedload(CartItemModel.movie))
    )
    cart = await db.scalar(stmt) or None

    if cart and any(item.movie_id == movie_id for item in cart.items):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Movie is already in the cart",
        )

    if not cart:
        cart = CartModel(user_id=user.id)

        db.add(cart)
        await db.flush()

    item = CartItemModel(movie_id=movie_id, cart_id=cart.id)

    db.add(item)

    await db.commit()

    return MessageResponseSchema(message="Item added successfully")

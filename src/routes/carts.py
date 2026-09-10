from fastapi import Depends, HTTPException, APIRouter
from sqlalchemy import select, exists
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload, joinedload
from starlette import status

from database.models.accounts import UserModel
from database.models.carts import CartModel, CartItemModel
from database.models.movies import MovieModel
from database.models.payments import PaymentItemModel, PaymentModel, PaymentStatusEnum
from database.session import get_db
from schemas.accounts import MessageResponseSchema
from schemas.carts import CartResponseSchema
from security.dependencies import get_current_user

router = APIRouter(
    prefix="/cart",
)


@router.get(
    "",
    status_code=status.HTTP_200_OK,
    response_model=CartResponseSchema,
    summary="Get user cart",
    description="Retrieves the current user's shopping cart along with items, nested movie details, genres, and certification.",
    responses={
        status.HTTP_200_OK: {
            "model": CartResponseSchema,
            "description": "User cart retrieved successfully.",
        },
        status.HTTP_401_UNAUTHORIZED: {
            "description": "Authentication token missing or invalid.",
        },
        status.HTTP_404_NOT_FOUND: {
            "description": "Cart not found for the user.",
            "content": {"application/json": {"example": {"detail": "Cart not found"}}},
        },
    },
)
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
    "/items",
    status_code=status.HTTP_201_CREATED,
    response_model=MessageResponseSchema,
    summary="Add item to cart",
    description="Adds a movie to the user's cart. Checks if the movie exists, if it has already been purchased by the user, or if it is already present in the cart.",
    responses={
        status.HTTP_201_CREATED: {
            "model": MessageResponseSchema,
            "description": "Item added to cart successfully.",
            "content": {
                "application/json": {"example": {"message": "Item added successfully"}}
            },
        },
        status.HTTP_400_BAD_REQUEST: {
            "description": "Movie already purchased or already in the cart.",
            "content": {
                "application/json": {
                    "examples": {
                        "already_purchased": {
                            "value": {"detail": "Movie is already is purchased."}
                        },
                        "already_in_cart": {
                            "value": {"detail": "Movie is already in the cart"}
                        },
                    }
                }
            },
        },
        status.HTTP_401_UNAUTHORIZED: {
            "description": "Authentication token missing or invalid.",
        },
        status.HTTP_404_NOT_FOUND: {
            "description": "Movie not found.",
            "content": {"application/json": {"example": {"detail": "Movie not found"}}},
        },
    },
)
async def add_item_to_cart(
    movie_id: int,
    user: UserModel = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    movie = await db.get(MovieModel, movie_id)

    if not movie:
        raise HTTPException(status_code=404, detail="Movie not found")

    stmt = select(
        exists().where(
            PaymentItemModel.movie_id == movie_id,
            PaymentItemModel.payment.has(PaymentModel.user_id == user.id),
            PaymentItemModel.payment.has(
                PaymentModel.status == PaymentStatusEnum.SUCCESSFUL
            ),
        )
    )
    is_purchased = await db.scalar(stmt)

    if is_purchased:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Movie is already is purchased.",
        )

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


@router.delete(
    "",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Clear cart",
    description="Completely removes the user's shopping cart and all items within it.",
    responses={
        status.HTTP_204_NO_CONTENT: {
            "description": "Cart successfully cleared.",
        },
        status.HTTP_401_UNAUTHORIZED: {
            "description": "Authentication token missing or invalid.",
        },
        status.HTTP_404_NOT_FOUND: {
            "description": "Cart not found.",
            "content": {"application/json": {"example": {"detail": "Cart not found"}}},
        },
    },
)
async def clear_cart(
    user: UserModel = Depends(get_current_user), db: AsyncSession = Depends(get_db)
):
    stmt = select(CartModel).where(CartModel.user_id == user.id)
    cart = await db.scalar(stmt)

    if not cart:
        raise HTTPException(status_code=404, detail="Cart not found")

    await db.delete(cart)
    await db.commit()

    return


@router.delete(
    "/items/{item_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Remove item from cart",
    description="Removes a specific item from the user's shopping cart by item ID.",
    responses={
        status.HTTP_204_NO_CONTENT: {
            "description": "Item successfully removed from cart.",
        },
        status.HTTP_401_UNAUTHORIZED: {
            "description": "Authentication token missing or invalid.",
        },
        status.HTTP_404_NOT_FOUND: {
            "description": "Item not found in user's cart.",
            "content": {"application/json": {"example": {"detail": "Item not found"}}},
        },
    },
)
async def remove_item_from_cart(
    item_id: int,
    user: UserModel = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    stmt = (
        select(CartItemModel)
        .join(CartModel)
        .where(CartItemModel.id == item_id, CartModel.user_id == user.id)
    )

    item = await db.scalar(stmt)

    if not item:
        raise HTTPException(status_code=404, detail="Item not found")

    await db.delete(item)
    await db.commit()

    return

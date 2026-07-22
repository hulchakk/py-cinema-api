from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import joinedload
from starlette import status

from database.models.accounts import (
    UserModel,
    UserGroupModel,
    UserGroupEnum,
    ActivationTokenModel,
)
from database.session import get_db
from schemas.accounts import (
    UserRegisterResponseSchema,
    UserRequestSchema,
    UserActivateRequestSchema,
)

router = APIRouter(
    prefix="/accounts",
)


@router.post(
    "/register",
    status_code=status.HTTP_201_CREATED,
    response_model=UserRegisterResponseSchema,
)
async def register_user(
    user_data: UserRequestSchema, db: AsyncSession = Depends(get_db)
):
    stmt = select(UserModel).where(UserModel.email == user_data.email)
    existing_user = await db.scalar(stmt)

    if existing_user:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT, detail="Email already registered."
        )

    stmt = select(UserGroupModel).where(UserGroupModel.name == UserGroupEnum.USER)
    result = await db.execute(stmt)
    user_group = result.scalars().first()

    if not user_group:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Default user group not found.",
        )

    try:
        new_user = UserModel.create(
            email=str(user_data.email),
            raw_password=user_data.password.get_secret_value(),
            group_id=user_group.id,
        )
        db.add(new_user)
        await db.flush()

        activation_token = ActivationTokenModel(user_id=new_user.id)
        db.add(activation_token)

        await db.commit()
        await db.refresh(new_user)
    except SQLAlchemyError as e:
        await db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="An error occurred during user creation.",
        ) from e
    else:
        return new_user


@router.post(
    "/activate",
    status_code=status.HTTP_200_OK,
    response_model=UserRegisterResponseSchema,
)
async def activate_user(
    user_data: UserActivateRequestSchema, db: AsyncSession = Depends(get_db)
):
    stmt = (
        select(UserModel)
        .where(UserModel.email == user_data.email)
        .options(joinedload(UserModel.activation_token))
    )
    user = await db.scalar(stmt)

    if not user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="User not found.",
        )

    if user.is_active:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="This user is already activated.",
        )

    if (
        not user.activation_token
        or user.activation_token.token != user_data.token.get_secret_value()
        or user.activation_token.is_expired
    ):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid activation token.",
        )

    user.is_active = True
    await db.delete(user.activation_token)
    await db.commit()

    return user

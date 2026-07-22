from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select, cast
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import joinedload
from starlette import status

from config.dependencies import get_jwt_auth_manager, get_settings
from config.settings import Settings
from database.models.accounts import (
    UserModel,
    UserGroupModel,
    UserGroupEnum,
    ActivationTokenModel,
    RefreshTokenModel,
    PasswordResetTokenModel,
)
from database.session import get_db
from schemas.accounts import (
    UserResponseSchema,
    UserRequestSchema,
    UserActivateRequestSchema,
    UserLoginResponseSchema,
    ResetPasswordResponseSchema,
    ResetPasswordRequestSchema,
)
from security.interfaces import JWTAuthManagerInterface

router = APIRouter(
    prefix="/accounts",
)


@router.post(
    "/register",
    status_code=status.HTTP_201_CREATED,
    response_model=UserResponseSchema,
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
    response_model=UserResponseSchema,
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


@router.post(
    "/login",
    status_code=status.HTTP_200_OK,
    response_model=UserLoginResponseSchema,
)
async def login_user(
    login_data: UserRequestSchema,
    settings: Settings = Depends(get_settings),
    jwt_manager: JWTAuthManagerInterface = Depends(get_jwt_auth_manager),
    db: AsyncSession = Depends(get_db),
):
    stmt = select(UserModel).where(UserModel.email == login_data.email)
    user = await db.scalar(stmt)

    if not user or not user.verify_password(login_data.password.get_secret_value()):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid email or password.",
        )

    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="User account is not activated.",
        )

    jwt_refresh_token = jwt_manager.create_refresh_token({"user_id": user.id})

    try:
        refresh_token = RefreshTokenModel.create(
            user_id=user.id,
            days_valid=settings.LOGIN_TIME_DAYS,
            token=jwt_refresh_token,
        )
        db.add(refresh_token)
        await db.flush()
        await db.commit()
    except SQLAlchemyError:
        await db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="An error occurred while processing the request.",
        )

    jwt_access_token = jwt_manager.create_access_token({"user_id": user.id})
    return UserLoginResponseSchema(
        access_token=jwt_access_token,
        refresh_token=jwt_refresh_token,
    )


@router.post(
    "/password/request-reset",
    status_code=status.HTTP_200_OK,
    response_model=ResetPasswordResponseSchema,
)
async def request_password_reset(
    user_data: ResetPasswordRequestSchema, db: AsyncSession = Depends(get_db)
):
    response = ResetPasswordResponseSchema(
        message="If you are registered, you will receive an email.",
    )

    stmt = (
        select(UserModel)
        .where(UserModel.email == user_data.email)
        .options(joinedload(UserModel.password_reset_token))
    )
    user = await db.scalar(stmt)

    if not user or not user.is_active:
        return response

    if user.password_reset_token:
        await db.delete(user.password_reset_token)
        await db.flush()

    reset_token = PasswordResetTokenModel(user_id=user.id)
    db.add(reset_token)
    await db.commit()

    return response

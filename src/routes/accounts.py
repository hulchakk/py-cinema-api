from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException
from fastapi.security import OAuth2PasswordRequestForm
from pydantic import SecretStr
from sqlalchemy import select
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import joinedload
from starlette import status

from config.dependencies import (
    get_accounts_email_notificator,
    get_jwt_auth_manager,
    get_settings,
)
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
from exceptions.security import BaseSecurityError
from schemas.accounts import (
    UserResponseSchema,
    UserRequestSchema,
    UserActivateRequestSchema,
    UserLoginResponseSchema,
    MessageResponseSchema,
    ResetPasswordRequestSchema,
    ResetPasswordCompleteRequestSchema,
    ChangePasswordRequestSchema,
    TokenRefreshResponseSchema,
    TokenRefreshRequestSchema,
)
from security.dependencies import get_current_user
from security.interfaces import JWTAuthManagerInterface
from services.notifications.interfaces import EmailSenderInterface

router = APIRouter(
    prefix="/accounts",
)


@router.post(
    "/register",
    status_code=status.HTTP_201_CREATED,
    response_model=UserResponseSchema,
    summary="Register a new user",
    description="Registers a new user, assigns the default USER group, and triggers an activation email via background tasks.",
    responses={
        status.HTTP_201_CREATED: {
            "model": UserResponseSchema,
            "description": "User created successfully.",
        },
        status.HTTP_409_CONFLICT: {
            "model": MessageResponseSchema,
            "description": "Email is already registered.",
            "content": {
                "application/json": {"example": {"detail": "Email already registered."}}
            },
        },
        status.HTTP_500_INTERNAL_SERVER_ERROR: {
            "model": MessageResponseSchema,
            "description": "Server error during registration process.",
            "content": {
                "application/json": {
                    "examples": {
                        "missing_group": {
                            "value": {"detail": "Default user group not found."}
                        },
                        "db_error": {
                            "value": {
                                "detail": "An error occurred during user creation."
                            }
                        },
                    }
                }
            },
        },
    },
)
async def register_user(
    user_data: UserRequestSchema,
    background_tasks: BackgroundTasks,
    db: AsyncSession = Depends(get_db),
    email_sender: EmailSenderInterface = Depends(get_accounts_email_notificator),
    settings: Settings = Depends(get_settings),
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
        activation_link = f"{settings.FRONTEND_URL}/activate?email={new_user.email}&token={activation_token.token}"

        background_tasks.add_task(
            email_sender.send_activation_email,
            email=new_user.email,
            activation_link=activation_link,
        )
        return new_user


@router.post(
    "/activate",
    status_code=status.HTTP_200_OK,
    response_model=UserResponseSchema,
    summary="Activate account",
    description="Validates activation token and sets user status to active, then sends confirmation email.",
    responses={
        status.HTTP_200_OK: {
            "model": UserResponseSchema,
            "description": "Account activated successfully.",
        },
        status.HTTP_400_BAD_REQUEST: {
            "model": MessageResponseSchema,
            "description": "Invalid token or user status error.",
            "content": {
                "application/json": {
                    "examples": {
                        "user_not_found": {"value": {"detail": "User not found."}},
                        "already_activated": {
                            "value": {"detail": "This user is already activated."}
                        },
                        "invalid_token": {
                            "value": {"detail": "Invalid activation token."}
                        },
                    }
                }
            },
        },
    },
)
async def activate_user(
    user_data: UserActivateRequestSchema,
    background_tasks: BackgroundTasks,
    db: AsyncSession = Depends(get_db),
    email_sender: EmailSenderInterface = Depends(get_accounts_email_notificator),
    settings: Settings = Depends(get_settings),
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

    login_link = f"{settings.FRONTEND_URL}/login"

    background_tasks.add_task(
        email_sender.send_activation_complete_email,
        email=user.email,
        login_link=login_link,
    )

    return user


@router.post(
    "/login",
    status_code=status.HTTP_200_OK,
    response_model=UserLoginResponseSchema,
    summary="Login user",
    description="Authenticates user with OAuth2 form credentials and returns access/refresh JWT tokens.",
    responses={
        status.HTTP_200_OK: {
            "model": UserLoginResponseSchema,
            "description": "Successfully authenticated.",
        },
        status.HTTP_401_UNAUTHORIZED: {
            "model": MessageResponseSchema,
            "description": "Invalid user credentials.",
            "content": {
                "application/json": {
                    "example": {"detail": "Invalid email or password."}
                }
            },
        },
        status.HTTP_403_FORBIDDEN: {
            "model": MessageResponseSchema,
            "description": "User account is inactive.",
            "content": {
                "application/json": {
                    "example": {"detail": "User account is not activated."}
                }
            },
        },
        status.HTTP_500_INTERNAL_SERVER_ERROR: {
            "model": MessageResponseSchema,
            "description": "Database error storing refresh token.",
            "content": {
                "application/json": {
                    "example": {
                        "detail": "An error occurred while processing the request."
                    }
                }
            },
        },
    },
)
async def login_user(
    login_form: OAuth2PasswordRequestForm = Depends(),
    settings: Settings = Depends(get_settings),
    jwt_manager: JWTAuthManagerInterface = Depends(get_jwt_auth_manager),
    db: AsyncSession = Depends(get_db),
):
    login_data = UserRequestSchema(
        email=login_form.username,
        password=SecretStr(login_form.password),
    )
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
    "/refresh",
    status_code=status.HTTP_200_OK,
    response_model=TokenRefreshResponseSchema,
    summary="Refresh access token",
    description="Generates a new access JWT using a valid refresh JWT token.",
    responses={
        status.HTTP_200_OK: {
            "model": TokenRefreshResponseSchema,
            "description": "New access token issued.",
        },
        status.HTTP_400_BAD_REQUEST: {
            "model": MessageResponseSchema,
            "description": "Invalid JWT, missing refresh token, or expired token.",
            "content": {
                "application/json": {
                    "examples": {
                        "jwt_error": {"value": {"detail": "Invalid refresh token."}},
                        "token_not_found": {
                            "value": {"detail": "Refresh token not found."}
                        },
                    }
                }
            },
        },
        status.HTTP_404_NOT_FOUND: {
            "model": MessageResponseSchema,
            "description": "User associated with token does not exist or is inactive.",
            "content": {"application/json": {"example": {"detail": "User not found."}}},
        },
    },
)
async def refresh_access_token(
    user_data: TokenRefreshRequestSchema,
    jwt_manager: JWTAuthManagerInterface = Depends(get_jwt_auth_manager),
    db: AsyncSession = Depends(get_db),
):
    try:
        payload = jwt_manager.decode_refresh_token(
            user_data.refresh_token.get_secret_value()
        )
        user_id = payload.get("user_id")
    except BaseSecurityError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e),
        )

    stmt = select(UserModel).where(UserModel.id == user_id)
    user = await db.scalar(stmt)

    if not user or not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found.",
        )

    stmt = select(RefreshTokenModel).where(
        RefreshTokenModel.token == user_data.refresh_token.get_secret_value()
    )
    refresh_token = await db.scalar(stmt)

    token_not_found = HTTPException(
        status_code=status.HTTP_400_BAD_REQUEST,
        detail="Refresh token not found.",
    )

    if not refresh_token:
        raise token_not_found

    if refresh_token.is_expired:
        await db.delete(refresh_token)
        raise token_not_found

    jwt_access_token = jwt_manager.create_access_token({"user_id": user.id})
    return TokenRefreshResponseSchema(
        access_token=jwt_access_token,
    )


@router.post(
    "/password/request-reset",
    status_code=status.HTTP_200_OK,
    response_model=MessageResponseSchema,
    summary="Request password reset",
    description="Sends password reset link to user's email if registered and active. Always returns success message for security.",
    responses={
        status.HTTP_200_OK: {
            "model": MessageResponseSchema,
            "description": "Success message.",
            "content": {
                "application/json": {
                    "example": {
                        "message": "If you are registered, you will receive an email."
                    }
                }
            },
        },
    },
)
async def request_password_reset(
    user_data: ResetPasswordRequestSchema,
    background_tasks: BackgroundTasks,
    db: AsyncSession = Depends(get_db),
    email_sender: EmailSenderInterface = Depends(get_accounts_email_notificator),
    settings: Settings = Depends(get_settings),
):
    response = MessageResponseSchema(
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

    reset_link = f"{settings.FRONTEND_URL}/reset-password?email={user.email}&token={reset_token.token}"

    background_tasks.add_task(
        email_sender.send_password_reset_email,
        email=user.email,
        reset_link=reset_link,
    )

    return response


@router.post(
    "/password/reset-complete",
    status_code=status.HTTP_200_OK,
    response_model=MessageResponseSchema,
    summary="Complete password reset",
    description="Resets the password using a valid reset token and sends confirmation email.",
    responses={
        status.HTTP_200_OK: {
            "model": MessageResponseSchema,
            "description": "Password reset completed.",
            "content": {
                "application/json": {
                    "example": {"message": "Password reset successfully."}
                }
            },
        },
        status.HTTP_400_BAD_REQUEST: {
            "model": MessageResponseSchema,
            "description": "Invalid email, expired, or invalid token.",
            "content": {
                "application/json": {"example": {"detail": "Invalid email or token."}}
            },
        },
        status.HTTP_500_INTERNAL_SERVER_ERROR: {
            "model": MessageResponseSchema,
            "description": "Database error during password update.",
            "content": {
                "application/json": {
                    "example": {
                        "detail": "An error occurred while resetting the password."
                    }
                }
            },
        },
    },
)
async def reset_password_complete(
    user_data: ResetPasswordCompleteRequestSchema,
    background_tasks: BackgroundTasks,
    db: AsyncSession = Depends(get_db),
    email_sender: EmailSenderInterface = Depends(get_accounts_email_notificator),
    settings: Settings = Depends(get_settings),
):
    invalid_exception = HTTPException(
        status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid email or token."
    )

    stmt = (
        select(UserModel)
        .where(UserModel.email == user_data.email)
        .options(
            joinedload(UserModel.password_reset_token),
        )
    )
    user = await db.scalar(stmt)

    if not user or not user.is_active:
        raise invalid_exception

    token_record = user.password_reset_token

    if not token_record or token_record.token != user_data.token.get_secret_value():
        if token_record:
            await db.delete(token_record)
            await db.commit()
        raise invalid_exception

    if token_record.is_expired:
        await db.delete(token_record)
        await db.commit()

        raise invalid_exception

    try:
        user.password = user_data.password.get_secret_value()
        await db.delete(token_record)
        await db.commit()
    except SQLAlchemyError:
        await db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="An error occurred while resetting the password.",
        )

    login_link = f"{settings.FRONTEND_URL}/login"

    background_tasks.add_task(
        email_sender.send_password_reset_complete_email,
        email=user.email,
        login_link=login_link,
    )

    return MessageResponseSchema(message="Password reset successfully.")


@router.post(
    "/password/change",
    status_code=status.HTTP_200_OK,
    response_model=MessageResponseSchema,
    summary="Change password",
    description="Changes password for authenticated user.",
    responses={
        status.HTTP_200_OK: {
            "model": MessageResponseSchema,
            "description": "Password updated successfully.",
            "content": {
                "application/json": {
                    "example": {"message": "Password changed successfully."}
                }
            },
        },
        status.HTTP_400_BAD_REQUEST: {
            "model": MessageResponseSchema,
            "description": "Incorrect old password or new password matches the old password.",
            "content": {
                "application/json": {
                    "examples": {
                        "invalid_old": {"value": {"detail": "Invalid password."}},
                        "same_passwords": {
                            "value": {
                                "detail": "New password cannot be the same as the old password."
                            }
                        },
                    }
                }
            },
        },
        status.HTTP_401_UNAUTHORIZED: {
            "description": "Authentication token missing or invalid."
        },
    },
)
async def change_password(
    user_data: ChangePasswordRequestSchema,
    user: UserModel = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    if not user.verify_password(user_data.old_password.get_secret_value()):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid password."
        )

    if (
        user_data.old_password.get_secret_value()
        == user_data.new_password.get_secret_value()
    ):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="New password cannot be the same as the old password.",
        )

    user.password = user_data.new_password.get_secret_value()
    await db.commit()

    return MessageResponseSchema(message="Password changed successfully.")

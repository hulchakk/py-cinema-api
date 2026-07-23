from typing import List

from fastapi import Depends, HTTPException
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import joinedload
from starlette import status

from config.dependencies import get_jwt_auth_manager
from database.models.accounts import UserModel, UserGroupEnum
from database.session import get_db
from exceptions.security import TokenExpiredError, InvalidTokenError
from security.interfaces import JWTAuthManagerInterface

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/v1/accounts/login")


async def get_current_user(
    jwt_manager: JWTAuthManagerInterface = Depends(get_jwt_auth_manager),
    token: str = Depends(oauth2_scheme),
    db: AsyncSession = Depends(get_db),
) -> UserModel:
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
    )

    try:
        payload = jwt_manager.decode_access_token(token)
    except (TokenExpiredError, InvalidTokenError):
        raise credentials_exception

    stmt = (
        select(UserModel)
        .where(UserModel.id == payload["user_id"])
        .options(joinedload(UserModel.group))
    )
    user = await db.scalar(stmt)

    if not user or not user.is_active:
        raise credentials_exception

    return user


class PermissionChecker:
    def __init__(self, allowed_groups: List[UserGroupEnum]):
        self.allowed_groups = [group.value for group in allowed_groups]

    async def __call__(self, current_user: UserModel = Depends(get_current_user)):
        if current_user.group.name not in self.allowed_groups:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Not enough permissions",
            )

        return current_user


allow_staff = PermissionChecker(
    [
        UserGroupEnum.MODERATOR,
        UserGroupEnum.ADMIN,
    ]
)

allow_admin = PermissionChecker(
    [
        UserGroupEnum.ADMIN,
    ]
)

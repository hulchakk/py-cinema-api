from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from starlette import status

from database.models.accounts import UserModel
from database.models.profiles import UserProfileModel
from database.session import get_db
from schemas.profiles import UserProfileRetrieveResponseSchema
from security.dependencies import get_current_user

router = APIRouter(
    prefix="/me",
)


@router.get(
    "",
    status_code=status.HTTP_200_OK,
    response_model=UserProfileRetrieveResponseSchema,
)
async def get_user_profile(
    user: UserModel = Depends(get_current_user), db: AsyncSession = Depends(get_db)
):
    stmt = select(UserProfileModel).where(UserProfileModel.user_id == user.id)
    profile = await db.scalar(stmt)

    if not profile:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Profile not found."
        )

    return profile

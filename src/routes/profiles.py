from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select, exists
from sqlalchemy.ext.asyncio import AsyncSession
from starlette import status

from database.models.accounts import UserModel
from database.models.profiles import UserProfileModel
from database.session import get_db
from schemas.profiles import (
    UserProfileRetrieveResponseSchema,
    UserProfileCreateRequestSchema,
)
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


@router.post(
    "",
    status_code=status.HTTP_201_CREATED,
    response_model=UserProfileRetrieveResponseSchema,
)
async def create_user_profile(
    profile_data: UserProfileCreateRequestSchema,
    user: UserModel = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    stmt = select(exists().where(UserProfileModel.user_id == user.id))
    is_profile = await db.scalar(stmt)

    if is_profile:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Profile already exists.",
        )

    profile = UserProfileModel(
        user_id=user.id, **profile_data.model_dump(exclude_unset=True)
    )

    db.add(profile)

    await db.commit()
    await db.refresh(profile)

    return profile

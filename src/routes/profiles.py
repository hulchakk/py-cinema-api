from pathlib import Path
from uuid import uuid4

from fastapi import APIRouter, Depends, HTTPException, UploadFile, File
from sqlalchemy import select, exists
from sqlalchemy.ext.asyncio import AsyncSession
from starlette import status

from config.dependencies import get_s3_storage_client
from database.models.accounts import UserModel
from database.models.profiles import UserProfileModel
from database.session import get_db
from exceptions.storages import S3FileUploadError
from schemas.profiles import (
    UserProfileRetrieveResponseSchema,
    UserProfileCreateUpdateRequestSchema,
    UserProfileUpdateAvatarResponseSchema,
)
from security.dependencies import get_current_user
from services.storages.interfaces import S3StorageInterface

router = APIRouter(
    prefix="/me",
)


ProfileNotFound = HTTPException(
    status_code=status.HTTP_404_NOT_FOUND,
    detail="Profile not found.",
)


NoDataProvided = HTTPException(
    status_code=status.HTTP_400_BAD_REQUEST,
    detail="No data provided.",
)


@router.get(
    "",
    status_code=status.HTTP_200_OK,
    response_model=UserProfileRetrieveResponseSchema,
)
async def get_user_profile(
    storage: S3StorageInterface = Depends(get_s3_storage_client),
    user: UserModel = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    stmt = select(UserProfileModel).where(UserProfileModel.user_id == user.id)
    profile = await db.scalar(stmt)

    if not profile:
        raise ProfileNotFound

    avatar_url = storage.get_file_url(profile.avatar) if profile.avatar else None

    return UserProfileRetrieveResponseSchema(
        first_name=profile.first_name,
        last_name=profile.last_name,
        avatar_url=avatar_url,
        gender=profile.gender,
        date_of_birth=profile.date_of_birth,
        info=profile.info,
    )


@router.post(
    "",
    status_code=status.HTTP_201_CREATED,
    response_model=UserProfileRetrieveResponseSchema,
)
async def create_user_profile(
    profile_data: UserProfileCreateUpdateRequestSchema,
    storage: S3StorageInterface = Depends(get_s3_storage_client),
    user: UserModel = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    update_data = profile_data.model_dump(exclude_unset=True)
    if not update_data:
        raise NoDataProvided

    stmt = select(exists().where(UserProfileModel.user_id == user.id))
    is_profile = await db.scalar(stmt)

    if is_profile:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Profile already exists.",
        )

    profile = UserProfileModel(
        user_id=user.id,
        **update_data,
    )

    db.add(profile)
    await db.commit()
    await db.refresh(profile)

    avatar_url = storage.get_file_url(profile.avatar) if profile.avatar else None

    return UserProfileRetrieveResponseSchema(
        first_name=profile.first_name,
        last_name=profile.last_name,
        avatar_url=avatar_url,
        gender=profile.gender,
        date_of_birth=profile.date_of_birth,
        info=profile.info,
    )


@router.patch(
    "",
    status_code=status.HTTP_200_OK,
    response_model=UserProfileRetrieveResponseSchema,
)
async def update_user_profile(
    profile_data: UserProfileCreateUpdateRequestSchema,
    storage: S3StorageInterface = Depends(get_s3_storage_client),
    user: UserModel = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    update_data = profile_data.model_dump(exclude_unset=True)
    if not update_data:
        raise NoDataProvided

    stmt = select(UserProfileModel).where(UserProfileModel.user_id == user.id)
    profile = await db.scalar(stmt)

    if not profile:
        raise ProfileNotFound

    for key, value in update_data.items():
        setattr(profile, key, value)

    await db.commit()
    await db.refresh(profile)

    avatar_url = storage.get_file_url(profile.avatar) if profile.avatar else None

    return UserProfileRetrieveResponseSchema(
        first_name=profile.first_name,
        last_name=profile.last_name,
        avatar_url=avatar_url,
        gender=profile.gender,
        date_of_birth=profile.date_of_birth,
        info=profile.info,
    )

@router.post(
    "/avatar",
    status_code=status.HTTP_200_OK,
    response_model=UserProfileUpdateAvatarResponseSchema,
)
async def update_avatar(
    avatar_image: UploadFile = File(...),
    storage: S3StorageInterface = Depends(get_s3_storage_client),
    user: UserModel = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    stmt = select(UserProfileModel).where(UserProfileModel.user_id == user.id)
    profile = await db.scalar(stmt)

    if not profile:
        raise ProfileNotFound

    try:
        avatar_bytes = await avatar_image.read()
        ext = Path(avatar_image.filename).suffix

        file_name = f"avatars/{user.id}_avatar_{uuid4().hex[:8]}{ext}"

        await storage.upload_file(file_name=file_name, file_data=avatar_bytes)
    except S3FileUploadError:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to upload avatar. Please try again later.",
        )
    else:
        old_avatar = profile.avatar

        profile.avatar = file_name
        await db.commit()
        try:
            if old_avatar:
                await storage.delete_file(file_name=old_avatar)
        except:
            # TODO: Add a background task (Celery / BackgroundTasks) or a background cron script
            # for periodic cleanup of orphaned files from S3
            pass

    return UserProfileUpdateAvatarResponseSchema(
        avatar_url=storage.get_file_url(profile.avatar),
    )

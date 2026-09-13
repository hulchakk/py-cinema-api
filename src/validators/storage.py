import io
from fastapi import UploadFile, File, HTTPException
from PIL import Image, UnidentifiedImageError
from starlette import status

MAX_FILE_SIZE = 5 * 1024 * 1024  # 5 MB
ALLOWED_MIME_TYPES = {"image/jpeg", "image/png", "image/webp"}


async def validate_avatar(
    avatar_image: UploadFile = File(...),
) -> UploadFile:
    if avatar_image.content_type not in ALLOWED_MIME_TYPES:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Unsupported file type. Only JPEG, PNG, and WebP are allowed.",
        )

    contents = await avatar_image.read()

    if len(contents) > MAX_FILE_SIZE:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="File size exceeds the 5MB limit.",
        )

    try:
        image = Image.open(io.BytesIO(contents))
        image.verify()
    except (UnidentifiedImageError, Exception):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid or corrupted image file.",
        )

    await avatar_image.seek(0)
    return avatar_image

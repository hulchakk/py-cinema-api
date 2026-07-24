from fastapi import APIRouter, HTTPException
from fastapi import Depends
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.ext.asyncio import AsyncSession
from starlette import status

from database.models.movies import GenreModel, StarModel, DirectorModel
from database.session import get_db
from schemas.movies import (
    GenreCreateResponseSchema,
    GenreCreateRequestSchema,
    StarCreateResponseSchema,
    StarCreateRequestSchema,
    DirectorCreateResponseSchema,
    DirectorCreateRequestSchema,
)

router = APIRouter(
    prefix="/movies",
)


@router.post(
    "/genres",
    status_code=status.HTTP_201_CREATED,
    response_model=GenreCreateResponseSchema,
)
async def create_genre(
    user_data: GenreCreateRequestSchema, db: AsyncSession = Depends(get_db)
):
    new_genre = GenreModel(**user_data.model_dump())

    db.add(new_genre)
    try:
        await db.commit()
        await db.refresh(new_genre)
    except SQLAlchemyError:
        await db.rollback()
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"Genre with name '{user_data.name}' already exists.",
        )

    return new_genre


@router.post(
    "/stars",
    status_code=status.HTTP_201_CREATED,
    response_model=StarCreateResponseSchema,
)
async def create_star(
    user_data: StarCreateRequestSchema, db: AsyncSession = Depends(get_db)
):
    new_star = StarModel(**user_data.model_dump())

    db.add(new_star)
    try:
        await db.commit()
        await db.refresh(new_star)
    except SQLAlchemyError:
        await db.rollback()
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"Star with name '{user_data.name}' already exists.",
        )

    return new_star


@router.post(
    "/directors",
    status_code=status.HTTP_201_CREATED,
    response_model=DirectorCreateResponseSchema,
)
async def create_director(
    user_data: DirectorCreateRequestSchema, db: AsyncSession = Depends(get_db)
):
    new_director = DirectorModel(**user_data.model_dump())

    db.add(new_director)
    try:
        await db.commit()
        await db.refresh(new_director)
    except SQLAlchemyError:
        await db.rollback()
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"Director with name '{user_data.name}' already exists.",
        )

    return new_director

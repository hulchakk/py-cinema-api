import uuid
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import joinedload, selectinload
from starlette import status
from starlette.requests import Request

from database.models.movies import DirectorModel, GenreModel, MovieModel, StarModel
from database.session import get_db
from routes.dependencies import MovieFilterParams, PaginationParams
from schemas.movies import (
    DirectorResponseSchema,
    GenreResponseSchema,
    MovieListResponseSchema,
    MovieRetrieveResponseSchema,
    StarResponseSchema,
)
from schemas.pagination import PaginatedResponseSchema
from utils.paginator import paginate_response

router = APIRouter()


async def get_paginated_response(
    model,
    request: Request,
    pagination: PaginationParams,
    search: Optional[str],
    db: AsyncSession,
):
    stmt = select(func.count(model.id))
    if search:
        stmt = stmt.where(model.name.ilike(f"%{search}%"))

    total = await db.scalar(stmt) or 0

    if total == 0:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"{model.__name__.replace('Model', 's')} not found.",
        )

    stmt = select(model).offset(pagination.offset).limit(pagination.limit)
    if search:
        stmt = stmt.where(model.name.ilike(f"%{search}%"))

    results = list((await db.scalars(stmt)).all()) or []

    return paginate_response(
        request=request, results=results, total=total, pagination=pagination
    )


@router.get(
    "/movies",
    status_code=status.HTTP_200_OK,
    response_model=PaginatedResponseSchema[MovieListResponseSchema],
)
async def list_movies(
    request: Request,
    pagination: PaginationParams = Depends(),
    search: Optional[str] = Query(default=None),
    filtering: MovieFilterParams = Depends(),
    db: AsyncSession = Depends(get_db),
):
    stmt = select(func.count(MovieModel.id))
    stmt = filtering.apply_filters(stmt, MovieModel)

    if search:
        stmt = stmt.where(MovieModel.name.ilike(f"%{search}%"))

    total = await db.scalar(stmt) or 0

    if total == 0:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Movies not found."
        )

    stmt = (
        select(MovieModel)
        .offset(pagination.offset)
        .limit(pagination.limit)
        .options(
            selectinload(MovieModel.certification),
            selectinload(MovieModel.genres),
        )
    )
    stmt = filtering.apply_filters(stmt, MovieModel)

    if search:
        stmt = stmt.where(MovieModel.name.ilike(f"%{search}%"))

    results = list((await db.scalars(stmt)).all()) or []

    return paginate_response(
        request=request, results=results, total=total, pagination=pagination
    )


@router.get(
    "/movies/{movie_uuid}",
    status_code=status.HTTP_200_OK,
    response_model=MovieRetrieveResponseSchema,
)
async def get_movie_details(movie_uuid: uuid.UUID, db: AsyncSession = Depends(get_db)):
    stmt = (
        select(MovieModel)
        .where(MovieModel.uuid == movie_uuid)
        .options(
            joinedload(MovieModel.certification),
            selectinload(MovieModel.genres),
            selectinload(MovieModel.directors),
            selectinload(MovieModel.stars),
        )
    )
    movie = await db.scalar(stmt) or None

    if not movie:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Movie not found."
        )

    return movie


@router.get(
    "/genres",
    status_code=status.HTTP_200_OK,
    response_model=PaginatedResponseSchema[GenreResponseSchema],
)
async def list_genres(
    request: Request,
    pagination: PaginationParams = Depends(),
    search: Optional[str] = Query(default=None),
    db: AsyncSession = Depends(get_db),
):
    return await get_paginated_response(GenreModel, request, pagination, search, db)


@router.get(
    "/stars",
    status_code=status.HTTP_200_OK,
    response_model=PaginatedResponseSchema[StarResponseSchema],
)
async def list_stars(
    request: Request,
    pagination: PaginationParams = Depends(),
    search: Optional[str] = Query(default=None),
    db: AsyncSession = Depends(get_db),
):
    return await get_paginated_response(StarModel, request, pagination, search, db)


@router.get(
    "/directors",
    status_code=status.HTTP_200_OK,
    response_model=PaginatedResponseSchema[DirectorResponseSchema],
)
async def list_directors(
    request: Request,
    pagination: PaginationParams = Depends(),
    search: Optional[str] = Query(default=None),
    db: AsyncSession = Depends(get_db),
):
    return await get_paginated_response(DirectorModel, request, pagination, search, db)

import uuid
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload, joinedload
from starlette import status
from starlette.requests import Request

from database.models.movies import MovieModel
from database.session import get_db
from routes.dependencies import PaginationParams, MovieFilterParams
from schemas.movies import (
    PaginatedResponseSchema,
    MovieRetrieveResponseSchema,
    MovieListResponseSchema,
)

router = APIRouter(
    prefix="/movies",
)


@router.get(
    "",
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

    stmt = (
        select(MovieModel)
        .offset(pagination.offset)
        .limit(pagination.limit)
        .options(
            joinedload(MovieModel.certification),
            selectinload(MovieModel.genres),
        )
    )
    stmt = filtering.apply_filters(stmt, MovieModel)

    if search:
        stmt = stmt.where(MovieModel.name.ilike(f"%{search}%"))

    results = list((await db.scalars(stmt)).all()) or []

    if len(results) == 0:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Movies not found."
        )

    has_next = (pagination.page * pagination.per_page) < total
    has_prev = pagination.page > 1

    next_page = None
    if has_next:
        next_page = str(
            request.url.include_query_params(
                page=pagination.page + 1,
                per_page=pagination.per_page,
            )
        )

    previous_page = None
    if has_prev:
        previous_page = str(
            request.url.include_query_params(
                page=pagination.page - 1,
                per_page=pagination.per_page,
            )
        )

    return PaginatedResponseSchema(
        results=results,
        total=total,
        per_page=pagination.per_page,
        page=pagination.page,
        previous_page=previous_page,
        next_page=next_page,
    )


@router.get(
    "/{movie_uuid}",
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

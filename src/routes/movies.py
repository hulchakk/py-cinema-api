import uuid
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query, Path
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
    summary="List movies",
    description="Retrieves a paginated list of movies with optional filtering by various parameters and search by movie name. Includes movie certification and genres in the response.",
    responses={
        status.HTTP_200_OK: {
            "description": "Paginated list of movies retrieved successfully.",
        },
        status.HTTP_404_NOT_FOUND: {
            "description": "No movies match the specified criteria.",
            "content": {
                "application/json": {"example": {"detail": "Movies not found."}}
            },
        },
    },
)
async def list_movies(
    request: Request,
    pagination: PaginationParams = Depends(),
    search: Optional[str] = Query(
        default=None,
        title="Search Query",
        description="Search for movies by name (case-insensitive partial match).",
        examples=["Inception"],
    ),
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
    summary="Get movie details",
    description="Retrieves detailed information about a specific movie by its UUID, including certification, genres, directors, and stars.",
    responses={
        status.HTTP_200_OK: {
            "model": MovieRetrieveResponseSchema,
            "description": "Detailed movie information retrieved successfully.",
        },
        status.HTTP_404_NOT_FOUND: {
            "description": "Movie not found.",
            "content": {
                "application/json": {"example": {"detail": "Movie not found."}}
            },
        },
    },
)
async def get_movie_details(
    movie_uuid: uuid.UUID = Path(
        ...,
        title="Movie UUID",
        description="The unique identifier (UUID) of the movie.",
        examples=["123e4567-e89b-12d3-a456-426614174000"],
    ),
    db: AsyncSession = Depends(get_db),
):
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
    summary="List movie genres",
    description="Retrieves a paginated list of movie genres with optional search filtering by genre name.",
    responses={
        status.HTTP_200_OK: {
            "description": "Paginated list of genres retrieved successfully.",
        },
        status.HTTP_404_NOT_FOUND: {
            "description": "No genres found.",
            "content": {
                "application/json": {"example": {"detail": "Genres not found."}}
            },
        },
    },
)
async def list_genres(
    request: Request,
    pagination: PaginationParams = Depends(),
    search: Optional[str] = Query(
        default=None,
        title="Search Query",
        description="Search for genres by name (case-insensitive partial match).",
        examples=["Action"],
    ),
    db: AsyncSession = Depends(get_db),
):
    return await get_paginated_response(GenreModel, request, pagination, search, db)


@router.get(
    "/stars",
    status_code=status.HTTP_200_OK,
    response_model=PaginatedResponseSchema[StarResponseSchema],
    summary="List movie stars",
    description="Retrieves a paginated list of actors/stars with optional search filtering by star name.",
    responses={
        status.HTTP_200_OK: {
            "description": "Paginated list of stars retrieved successfully.",
        },
        status.HTTP_404_NOT_FOUND: {
            "description": "No stars found.",
            "content": {
                "application/json": {"example": {"detail": "Stars not found."}}
            },
        },
    },
)
async def list_stars(
    request: Request,
    pagination: PaginationParams = Depends(),
    search: Optional[str] = Query(
        default=None,
        title="Search Query",
        description="Search for stars/actors by name (case-insensitive partial match).",
        examples=["Leonardo DiCaprio"],
    ),
    db: AsyncSession = Depends(get_db),
):
    return await get_paginated_response(StarModel, request, pagination, search, db)


@router.get(
    "/directors",
    status_code=status.HTTP_200_OK,
    response_model=PaginatedResponseSchema[DirectorResponseSchema],
    summary="List movie directors",
    description="Retrieves a paginated list of movie directors with optional search filtering by director name.",
    responses={
        status.HTTP_200_OK: {
            "description": "Paginated list of directors retrieved successfully.",
        },
        status.HTTP_404_NOT_FOUND: {
            "description": "No directors found.",
            "content": {
                "application/json": {"example": {"detail": "Directors not found."}}
            },
        },
    },
)
async def list_directors(
    request: Request,
    pagination: PaginationParams = Depends(),
    search: Optional[str] = Query(
        default=None,
        title="Search Query",
        description="Search for directors by name (case-insensitive partial match).",
        examples=["Christopher Nolan"],
    ),
    db: AsyncSession = Depends(get_db),
):
    return await get_paginated_response(DirectorModel, request, pagination, search, db)

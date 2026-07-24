from fastapi import APIRouter, Depends
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload
from starlette import status
from starlette.requests import Request

from database.models.movies import MovieModel
from database.session import get_db
from routes.dependencies import PaginationParams
from schemas.movies import PaginatedResponseSchema, MovieRetrieveResponseSchema

router = APIRouter(
    prefix="/movies",
)


@router.get(
    "",
    status_code=status.HTTP_200_OK,
    response_model=PaginatedResponseSchema[MovieRetrieveResponseSchema],
)
async def movies(
    request: Request,
    pagination: PaginationParams = Depends(),
    db: AsyncSession = Depends(get_db),
):
    stmt = select(func.count(MovieModel.id))
    total = await db.scalar(stmt) or 0

    stmt = (
        select(MovieModel)
        .offset(pagination.offset)
        .limit(pagination.limit)
        .options(
            selectinload(MovieModel.genres),
            selectinload(MovieModel.directors),
            selectinload(MovieModel.stars),
        )
    )
    results = list((await db.scalars(stmt)).all()) or []

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

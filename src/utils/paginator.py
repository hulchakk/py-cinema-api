from typing import Sequence
from starlette.requests import Request

from routes.dependencies import PaginationParams
from schemas.pagination import PaginatedResponseSchema, T


def paginate_response(
    request: Request,
    results: Sequence[T],
    total: int,
    pagination: PaginationParams,
) -> PaginatedResponseSchema[T]:
    has_next = (pagination.page * pagination.per_page) < total
    has_prev = pagination.page > 1

    next_page = (
        str(
            request.url.include_query_params(
                page=pagination.page + 1,
                per_page=pagination.per_page,
            )
        )
        if has_next
        else None
    )

    previous_page = (
        str(
            request.url.include_query_params(
                page=pagination.page - 1,
                per_page=pagination.per_page,
            )
        )
        if has_prev
        else None
    )

    return PaginatedResponseSchema[T](
        results=list(results),
        total=total,
        per_page=pagination.per_page,
        page=pagination.page,
        previous_page=previous_page,
        next_page=next_page,
    )

from typing import TypeVar, Generic, Optional

from pydantic import BaseModel

T = TypeVar("T")


class PaginatedResponseSchema(BaseModel, Generic[T]):
    results: list[T]
    page: int
    per_page: int
    total: int
    next_page: Optional[str] = None
    previous_page: Optional[str] = None

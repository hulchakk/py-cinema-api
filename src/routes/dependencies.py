from decimal import Decimal
from typing import Optional

from fastapi import Query


class PaginationParams:
    def __init__(
        self,
        page: int = Query(default=1, ge=1),
        per_page: int = Query(default=10, ge=1, le=100),
    ):
        self.page = page
        self.per_page = per_page
        self.offset = (page - 1) * per_page
        self.limit = per_page


class MovieFilterParams:
    def __init__(
        self,
        year_from: Optional[int] = Query(default=None, ge=1888, le=2100),
        year_to: Optional[int] = Query(default=None, ge=1888, le=2100),
        price_from: Optional[Decimal] = Query(default=None, ge=0),
        price_to: Optional[Decimal] = Query(default=None, gt=0),
        imdb_from: Optional[float] = Query(default=None, ge=0, le=10),
        imdb_to: Optional[float] = Query(default=None, gt=0, le=10),
        time_from: Optional[int] = Query(default=None, ge=0),
        time_to: Optional[int] = Query(default=None, gt=0),
        genres: Optional[list[int]] = Query(default=None),
    ):
        self.year_from = year_from
        self.year_to = year_to
        self.price_from = price_from
        self.price_to = price_to
        self.imdb_from = imdb_from
        self.imdb_to = imdb_to
        self.time_from = time_from
        self.time_to = time_to
        self.genres = genres

    def apply_filters(self, stmt, movie_model):
        if self.year_from:
            stmt = stmt.where(movie_model.year >= self.year_from)
        if self.year_to:
            stmt = stmt.where(movie_model.year <= self.year_to)

        if self.price_from is not None:
            stmt = stmt.where(movie_model.price >= self.price_from)
        if self.price_to is not None:
            stmt = stmt.where(movie_model.price <= self.price_to)

        if self.imdb_from is not None:
            stmt = stmt.where(movie_model.imdb >= self.imdb_from)
        if self.imdb_to is not None:
            stmt = stmt.where(movie_model.imdb <= self.imdb_to)

        if self.time_from:
            stmt = stmt.where(movie_model.time >= self.time_from)
        if self.time_to:
            stmt = stmt.where(movie_model.time <= self.time_to)

        if self.genres:
            stmt = stmt.where(
                movie_model.genres.any(
                    movie_model.genres.property.mapper.class_.id.in_(self.genres)
                )
            )

        return stmt

from decimal import Decimal
from typing import Optional

from fastapi import Query


class PaginationParams:
    def __init__(
        self,
        page: int = Query(
            default=1,
            ge=1,
            title="Page Number",
            description="Page number for pagination, starting from 1.",
            examples=[1],
        ),
        per_page: int = Query(
            default=10,
            ge=1,
            le=100,
            title="Items Per Page",
            description="Number of items to return per page (max 100).",
            examples=[10],
        ),
    ):
        self.page = page
        self.per_page = per_page
        self.offset = (page - 1) * per_page
        self.limit = per_page


class MovieFilterParams:
    def __init__(
        self,
        year_from: Optional[int] = Query(
            default=None,
            ge=1888,
            le=2100,
            title="Release Year From",
            description="Filter movies released in or after this year.",
            examples=[2000],
        ),
        year_to: Optional[int] = Query(
            default=None,
            ge=1888,
            le=2100,
            title="Release Year To",
            description="Filter movies released in or before this year.",
            examples=[2023],
        ),
        price_from: Optional[Decimal] = Query(
            default=None,
            ge=0,
            title="Minimum Price",
            description="Filter movies with a price greater than or equal to this value.",
            examples=[0.00],
        ),
        price_to: Optional[Decimal] = Query(
            default=None,
            gt=0,
            title="Maximum Price",
            description="Filter movies with a price less than or equal to this value.",
            examples=[19.99],
        ),
        imdb_from: Optional[float] = Query(
            default=None,
            ge=0,
            le=10,
            title="Minimum IMDb Rating",
            description="Filter movies with an IMDb score greater than or equal to this value.",
            examples=[7.0],
        ),
        imdb_to: Optional[float] = Query(
            default=None,
            gt=0,
            le=10,
            title="Maximum IMDb Rating",
            description="Filter movies with an IMDb score less than or equal to this value.",
            examples=[10.0],
        ),
        time_from: Optional[int] = Query(
            default=None,
            ge=0,
            title="Minimum Duration (minutes)",
            description="Filter movies with a runtime greater than or equal to this value in minutes.",
            examples=[90],
        ),
        time_to: Optional[int] = Query(
            default=None,
            gt=0,
            title="Maximum Duration (minutes)",
            description="Filter movies with a runtime less than or equal to this value in minutes.",
            examples=[180],
        ),
        genres: Optional[list[int]] = Query(
            default=None,
            title="Genre IDs",
            description="Filter movies that match any of the specified genre IDs.",
            examples=[[1, 2]],
        ),
        directors: Optional[list[int]] = Query(
            default=None,
            title="Director IDs",
            description="Filter movies directed by any of the specified director IDs.",
            examples=[[5]],
        ),
        stars: Optional[list[int]] = Query(
            default=None,
            title="Star IDs",
            description="Filter movies featuring any of the specified actor/star IDs.",
            examples=[[10, 12]],
        ),
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
        self.directors = directors
        self.stars = stars

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

        if self.directors:
            stmt = stmt.where(
                movie_model.directors.any(
                    movie_model.directors.property.mapper.class_.id.in_(self.directors)
                )
            )

        if self.stars:
            stmt = stmt.where(
                movie_model.stars.any(
                    movie_model.stars.property.mapper.class_.id.in_(self.stars)
                )
            )

        return stmt

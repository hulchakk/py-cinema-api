import uuid
from decimal import Decimal
from typing import Optional

from pydantic import BaseModel, Field, ConfigDict


class GenreBaseSchema(BaseModel):
    name: str


class GenreCreateResponseSchema(GenreBaseSchema):
    id: int


class GenreCreateRequestSchema(GenreBaseSchema):
    pass


class StarBaseSchema(BaseModel):
    name: str


class StarCreateResponseSchema(StarBaseSchema):
    id: int


class StarCreateRequestSchema(StarBaseSchema):
    pass


class DirectorBaseSchema(BaseModel):
    name: str


class DirectorCreateResponseSchema(DirectorBaseSchema):
    id: int


class DirectorCreateRequestSchema(DirectorBaseSchema):
    pass


class CertificationBaseSchema(BaseModel):
    name: str


class CertificationCreateResponseSchema(CertificationBaseSchema):
    id: int


class CertificationCreateRequestSchema(CertificationBaseSchema):
    pass


class MovieBaseSchema(BaseModel):
    name: str = Field(min_length=1, max_length=250)
    year: int = Field(ge=1888, le=2100)
    time: int = Field(gt=0)
    imdb: float = Field(ge=0.0, le=10.0)
    votes: int = Field(ge=0)
    meta_score: Optional[float] = Field(default=None, ge=0.0, le=100.0)
    gross: Optional[float] = Field(default=None, ge=0.0)
    description: str = Field(min_length=10)
    price: Optional[Decimal] = Field(
        default=None, ge=0, max_digits=10, decimal_places=2
    )
    certification_id: int = Field(gt=0)


class MovieCreateRequestSchema(MovieBaseSchema):
    genre_ids: list[int]
    director_ids: list[int]
    star_ids: list[int]


class MovieCreateResponseSchema(MovieBaseSchema):
    id: int
    uuid: uuid.UUID

    model_config = ConfigDict(from_attributes=True)

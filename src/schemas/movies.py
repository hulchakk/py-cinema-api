import uuid
from decimal import Decimal
from typing import Optional, TypeVar, Generic

from pydantic import BaseModel, ConfigDict, Field, field_validator


class GenreBaseSchema(BaseModel):
    name: str


class GenreCreateRequestSchema(GenreBaseSchema):
    pass


class GenreUpdateRequestSchema(GenreBaseSchema):
    pass


class GenreResponseSchema(GenreBaseSchema):
    id: int

    model_config = ConfigDict(from_attributes=True)


GenreCreateResponseSchema = GenreResponseSchema
GenreUpdateResponseSchema = GenreResponseSchema


class StarBaseSchema(BaseModel):
    name: str


class StarCreateRequestSchema(StarBaseSchema):
    pass


class StarUpdateRequestSchema(StarBaseSchema):
    pass


class StarResponseSchema(StarBaseSchema):
    id: int

    model_config = ConfigDict(from_attributes=True)


StarCreateResponseSchema = StarResponseSchema
StarUpdateResponseSchema = StarResponseSchema


class DirectorBaseSchema(BaseModel):
    name: str


class DirectorCreateRequestSchema(DirectorBaseSchema):
    pass


class DirectorUpdateRequestSchema(DirectorBaseSchema):
    pass


class DirectorResponseSchema(DirectorBaseSchema):
    id: int

    model_config = ConfigDict(from_attributes=True)


DirectorCreateResponseSchema = DirectorResponseSchema
DirectorUpdateResponseSchema = DirectorResponseSchema


class CertificationBaseSchema(BaseModel):
    name: str


class CertificationCreateRequestSchema(CertificationBaseSchema):
    pass


class CertificationUpdateRequestSchema(CertificationBaseSchema):
    pass


class CertificationResponseSchema(CertificationBaseSchema):
    id: int

    model_config = ConfigDict(from_attributes=True)


CertificationCreateResponseSchema = CertificationResponseSchema
CertificationUpdateResponseSchema = CertificationResponseSchema


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


class MovieUpdateRequestSchema(BaseModel):
    name: Optional[str] = Field(default=None, min_length=1, max_length=250)
    year: Optional[int] = Field(default=None, ge=1888, le=2100)
    time: Optional[int] = Field(default=None, gt=0)
    imdb: Optional[float] = Field(default=None, ge=0.0, le=10.0)
    votes: Optional[int] = Field(default=None, ge=0)
    meta_score: Optional[float] = Field(default=None, ge=0.0, le=100.0)
    gross: Optional[float] = Field(default=None, ge=0.0)
    description: Optional[str] = Field(default=None, min_length=10)
    price: Optional[Decimal] = Field(
        default=None, ge=0, max_digits=10, decimal_places=2
    )
    certification_id: Optional[int] = Field(default=None, gt=0)
    genre_ids: Optional[list[int]] = None
    director_ids: Optional[list[int]] = None
    star_ids: Optional[list[int]] = None


class MovieCreateResponseSchema(MovieBaseSchema):
    id: int
    uuid: uuid.UUID

    model_config = ConfigDict(from_attributes=True)


MovieUpdateResponseSchema = MovieCreateResponseSchema


class MovieRetrieveResponseSchema(MovieUpdateResponseSchema):
    genres: list[str]
    directors: list[str]
    stars: list[str]

    @field_validator("genres", "directors", "stars", mode="before")
    @classmethod
    def convert_models_to_names(cls, value):
        if value and hasattr(value[0], "name"):
            return [item.name for item in value]
        return value


T = TypeVar("T")


class PaginatedResponseSchema(BaseModel, Generic[T]):
    results: list[T]
    page: int
    per_page: int
    total: int
    next_page: Optional[str] = None
    previous_page: Optional[str] = None

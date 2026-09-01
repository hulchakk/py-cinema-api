from typing import List

from pydantic import BaseModel, ConfigDict

from schemas.movies import MovieListResponseSchema


class CartItemResponseSchema(BaseModel):
    id: int
    movie: MovieListResponseSchema

    model_config = ConfigDict(from_attributes=True)


class CartResponseSchema(BaseModel):
    items: List[CartItemResponseSchema]

    model_config = ConfigDict(from_attributes=True)

from typing import List

from pydantic import BaseModel, ConfigDict

from schemas.movies import MovieListResponseSchema


class CartResponseSchema(BaseModel):
    items: List[MovieListResponseSchema]

    model_config = ConfigDict(from_attributes=True)

from pydantic import BaseModel


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

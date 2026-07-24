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

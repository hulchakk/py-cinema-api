from pydantic import BaseModel, EmailStr


class UserRequestSchema(BaseModel):
    email: EmailStr
    password: str


class UserRegisterResponseSchema(BaseModel):
    id: int
    email: EmailStr

from pydantic import BaseModel, EmailStr, SecretStr


class UserRequestSchema(BaseModel):
    email: EmailStr
    password: SecretStr


class UserRegisterResponseSchema(BaseModel):
    id: int
    email: EmailStr

from pydantic import BaseModel, EmailStr, SecretStr


class UserRequestSchema(BaseModel):
    email: EmailStr
    password: SecretStr


class UserResponseSchema(BaseModel):
    id: int
    email: EmailStr

    model_config = {"from_attributes": True}


class UserActivateRequestSchema(BaseModel):
    email: EmailStr
    token: SecretStr

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


class UserLoginResponseSchema(BaseModel):
    access_token: str
    refresh_token: str


class ResetPasswordRequestSchema(BaseModel):
    email: EmailStr


class ResetPasswordResponseSchema(BaseModel):
    message: str


class ResetPasswordCompleteRequestSchema(BaseModel):
    email: EmailStr
    token: SecretStr
    password: SecretStr

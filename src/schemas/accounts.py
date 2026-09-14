from pydantic import BaseModel, EmailStr, SecretStr, field_validator

from validators import validate_password


class UserRequestSchema(BaseModel):
    email: EmailStr
    password: SecretStr

    @field_validator("password")
    @classmethod
    def validate_password_field(cls, v: SecretStr) -> SecretStr:
        validate_password(v.get_secret_value())
        return v


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


class MessageResponseSchema(BaseModel):
    message: str


class ResetPasswordCompleteRequestSchema(BaseModel):
    email: EmailStr
    token: SecretStr
    password: SecretStr

    @field_validator("password")
    @classmethod
    def validate_password_field(cls, v: SecretStr) -> SecretStr:
        validate_password(v.get_secret_value())
        return v


class ChangePasswordRequestSchema(BaseModel):
    old_password: SecretStr
    new_password: SecretStr

    @field_validator("new_password")
    @classmethod
    def validate_password_field(cls, v: SecretStr) -> SecretStr:
        validate_password(v.get_secret_value())
        return v


class TokenRefreshRequestSchema(BaseModel):
    refresh_token: SecretStr


class TokenRefreshResponseSchema(BaseModel):
    access_token: str

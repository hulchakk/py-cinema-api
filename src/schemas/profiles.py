from datetime import date
from typing import Optional

from pydantic import BaseModel, ConfigDict

from database.models.profiles import GenderEnum


class UserProfileRetrieveResponseSchema(BaseModel):
    first_name: Optional[str] = None
    last_name: Optional[str] = None
    avatar_url: Optional[str] = None
    gender: Optional[GenderEnum] = None
    date_of_birth: Optional[date] = None
    info: Optional[str] = None


class UserProfileCreateUpdateRequestSchema(BaseModel):
    first_name: Optional[str] = None
    last_name: Optional[str] = None
    gender: Optional[GenderEnum] = None
    date_of_birth: Optional[date] = None
    info: Optional[str] = None


class UserProfileUpdateAvatarResponseSchema(BaseModel):
    avatar_url: str

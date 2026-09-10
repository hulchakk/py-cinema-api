import enum
from datetime import date
from typing import Optional, TYPE_CHECKING
from sqlalchemy import String, Enum, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column, relationship

from database.models.base import Base

if TYPE_CHECKING:
    from database.models.accounts import UserModel


class GenderEnum(str, enum.Enum):
    MALE = "male"
    FEMALE = "female"


class UserProfileModel(Base):
    __tablename__ = "user_profiles"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    user_id: Mapped[int] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"),
        unique=True,
        nullable=False,
    )
    first_name: Mapped[Optional[str]] = mapped_column(String(50))
    last_name: Mapped[Optional[str]] = mapped_column(String(50))
    avatar: Mapped[Optional[str]] = mapped_column(String(255))
    gender: Mapped[Optional[GenderEnum]] = mapped_column(Enum(GenderEnum))
    date_of_birth: Mapped[Optional[date]] = mapped_column()
    info: Mapped[Optional[str]] = mapped_column()

    user: Mapped["UserModel"] = relationship(
        "UserModel",
        back_populates="profile",
    )

    @property
    def avatar_url(self):
        return self.avatar

import enum

from sqlalchemy import Enum
from sqlalchemy.orm import Mapped, mapped_column

from database.models.base import Base


class UserGroupEnum(str, enum.Enum):
    USER = "user"
    MODERATOR = "moderator"
    ADMIN = "admin"


class UserGroupModel(Base):
    __tablename__ = "user_groups"

    id: Mapped[int] = mapped_column(primary_key=True, auto_increment=True)
    name: Mapped[str] = mapped_column(Enum(UserGroupEnum), unique=True)

    def __repr__(self) -> str:
        return f"<UserGroupModel(id={self.id}, name={self.name})>"

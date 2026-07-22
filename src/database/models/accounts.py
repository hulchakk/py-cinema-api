from __future__ import annotations

import enum
from datetime import datetime
from typing import List

from sqlalchemy import String, DateTime, ForeignKey, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from database.models.base import Base
from security.passwords import hash_password


class UserGroupEnum(str, enum.Enum):
    USER = "user"
    MODERATOR = "moderator"
    ADMIN = "admin"


class UserGroupModel(Base):
    __tablename__ = "user_groups"

    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(50), unique=True)

    users: Mapped[List[UserModel]] = relationship("UserModel", back_populates="group")

    def __repr__(self) -> str:
        return f"<UserGroupModel(id={self.id}, name={self.name})>"


class UserModel(Base):
    __tablename__ = "users"

    id: Mapped[int] = mapped_column(primary_key=True)
    email: Mapped[str] = mapped_column(String(255), unique=True, index=True)
    _hashed_password: Mapped[str] = mapped_column(String(60))

    is_active: Mapped[bool] = mapped_column(default=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )

    group_id: Mapped[int] = mapped_column(
        ForeignKey("user_groups.id", ondelete="CASCADE"), nullable=False
    )
    group: Mapped[UserGroupModel] = relationship(UserGroupModel, back_populates="users")

    def __repr__(self) -> str:
        return (
            f"<UserModel(id={self.id}, email={self.email}), is_active={self.is_active}>"
        )

    @property
    def password(self):
        raise AttributeError("Password reading is restricted")

    @password.setter
    def password(self, raw_password: str):
        self._hashed_password = hash_password(raw_password)

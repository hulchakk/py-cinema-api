from typing import TYPE_CHECKING, List
from sqlalchemy import ForeignKey, UniqueConstraint
from sqlalchemy.orm import mapped_column, Mapped, relationship

from database.models.base import Base

if TYPE_CHECKING:
    from database.models.accounts import UserModel
    from database.models.movies import MovieModel


class CartModel(Base):
    __tablename__ = "carts"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)

    user_id: Mapped[int] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"), unique=True, nullable=False
    )
    user: Mapped["UserModel"] = relationship("UserModel", back_populates="cart")

    items: Mapped[List["CartItemModel"]] = relationship(
        "CartItemModel", back_populates="cart", cascade="all, delete-orphan"
    )


class CartItemModel(Base):
    __tablename__ = "cart_items"
    __table_args__ = (UniqueConstraint("cart_id", "movie_id", name="uq_cart_movie"),)

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)

    cart_id: Mapped[int] = mapped_column(
        ForeignKey("carts.id", ondelete="CASCADE"), nullable=False
    )
    movie_id: Mapped[int] = mapped_column(
        ForeignKey("movies.id", ondelete="CASCADE"), nullable=False
    )

    cart: Mapped["CartModel"] = relationship("CartModel", back_populates="items")
    movie: Mapped["MovieModel"] = relationship("MovieModel")

import uuid as Pyuuid
from decimal import Decimal
from typing import Optional

from sqlalchemy import Column, Table, ForeignKey, String, Text, UniqueConstraint
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from database.models.base import Base

movie_genres = Table(
    "movie_genres",
    Base.metadata,
    Column("movie_id", ForeignKey("movies.id"), primary_key=True, nullable=False),
    Column("genre_id", ForeignKey("genres.id"), primary_key=True, nullable=False),
)

movie_directors = Table(
    "movie_directors",
    Base.metadata,
    Column("movie_id", ForeignKey("movies.id"), primary_key=True, nullable=False),
    Column("director_id", ForeignKey("directors.id"), primary_key=True, nullable=False),
)

movie_stars = Table(
    "movie_stars",
    Base.metadata,
    Column("movie_id", ForeignKey("movies.id"), primary_key=True, nullable=False),
    Column("star_id", ForeignKey("stars.id"), primary_key=True, nullable=False),
)


class GenreModel(Base):
    __tablename__ = "genres"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    name: Mapped[str] = mapped_column(String(100), unique=True, nullable=False)

    movies: Mapped[list["MovieModel"]] = relationship(
        secondary=movie_genres, back_populates="genres"
    )


class StarModel(Base):
    __tablename__ = "stars"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    name: Mapped[str] = mapped_column(String(100), unique=True, nullable=False)

    movies: Mapped[list["MovieModel"]] = relationship(
        secondary=movie_stars, back_populates="stars"
    )


class DirectorModel(Base):
    __tablename__ = "directors"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    name: Mapped[str] = mapped_column(String(100), unique=True, nullable=False)

    movies: Mapped[list["MovieModel"]] = relationship(
        secondary=movie_directors, back_populates="directors"
    )


class CertificationModel(Base):
    __tablename__ = "certifications"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    name: Mapped[str] = mapped_column(String(100), unique=True, nullable=False)

    movies: Mapped[list["MovieModel"]] = relationship(back_populates="certification")


class MovieModel(Base):
    __tablename__ = "movies"
    __table_args__ = (
        UniqueConstraint("name", "year", "time", name="uq_movies_name_year_time"),
    )

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    uuid: Mapped[Pyuuid.UUID] = mapped_column(
        UUID(as_uuid=True), default=Pyuuid.uuid4, unique=True, nullable=False
    )
    name: Mapped[str] = mapped_column(String(250), nullable=False)
    year: Mapped[int] = mapped_column(nullable=False)
    time: Mapped[int] = mapped_column(nullable=False)
    imdb: Mapped[float] = mapped_column(nullable=False)
    votes: Mapped[int] = mapped_column(nullable=False)
    meta_score: Mapped[Optional[float]] = mapped_column(nullable=True)
    gross: Mapped[Optional[float]] = mapped_column(nullable=True)
    description: Mapped[str] = mapped_column(Text, nullable=False)
    price: Mapped[Optional[Decimal]] = mapped_column(nullable=True)
    certification_id: Mapped[int] = mapped_column(
        ForeignKey("certifications.id"), nullable=False
    )

    certification: Mapped["CertificationModel"] = relationship(back_populates="movies")
    genres: Mapped[list["GenreModel"]] = relationship(
        secondary=movie_genres, back_populates="movies"
    )
    directors: Mapped[list["DirectorModel"]] = relationship(
        secondary=movie_directors, back_populates="movies"
    )
    stars: Mapped[list["StarModel"]] = relationship(
        secondary=movie_stars, back_populates="movies"
    )

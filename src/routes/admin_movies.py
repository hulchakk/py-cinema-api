from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select, exists
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.ext.asyncio import AsyncSession
from starlette import status

from database.models.movies import (
    CertificationModel,
    DirectorModel,
    GenreModel,
    MovieModel,
    StarModel,
)
from database.models.payments import PaymentItemModel, PaymentModel, PaymentStatusEnum
from database.session import get_db
from schemas.movies import (
    CertificationCreateRequestSchema,
    CertificationCreateResponseSchema,
    CertificationUpdateRequestSchema,
    CertificationUpdateResponseSchema,
    DirectorCreateRequestSchema,
    DirectorCreateResponseSchema,
    DirectorUpdateRequestSchema,
    DirectorUpdateResponseSchema,
    GenreCreateRequestSchema,
    GenreCreateResponseSchema,
    GenreUpdateRequestSchema,
    GenreUpdateResponseSchema,
    MovieCreateRequestSchema,
    MovieCreateResponseSchema,
    MovieUpdateRequestSchema,
    MovieUpdateResponseSchema,
    StarCreateRequestSchema,
    StarCreateResponseSchema,
    StarUpdateRequestSchema,
    StarUpdateResponseSchema,
)

router = APIRouter(
    prefix="/movies",
)


@router.post(
    "/genres",
    status_code=status.HTTP_201_CREATED,
    response_model=GenreCreateResponseSchema,
)
async def create_genre(
    user_data: GenreCreateRequestSchema, db: AsyncSession = Depends(get_db)
):
    new_genre = GenreModel(**user_data.model_dump())

    db.add(new_genre)
    try:
        await db.commit()
        await db.refresh(new_genre)
    except SQLAlchemyError:
        await db.rollback()
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"Genre with name '{user_data.name}' already exists.",
        )

    return new_genre


@router.put(
    "/genres/{genre_id}",
    response_model=GenreUpdateResponseSchema,
)
async def update_genre(
    genre_id: int,
    user_data: GenreUpdateRequestSchema,
    db: AsyncSession = Depends(get_db),
):
    stmt = select(GenreModel).where(GenreModel.id == genre_id)
    genre = await db.scalar(stmt)

    if not genre:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Genre with id {genre_id} not found.",
        )

    for key, value in user_data.model_dump().items():
        setattr(genre, key, value)

    try:
        await db.commit()
        await db.refresh(genre)
    except SQLAlchemyError:
        await db.rollback()
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"Genre with name '{user_data.name}' already exists.",
        )

    return genre


@router.delete(
    "/genres/{genre_id}",
    status_code=status.HTTP_204_NO_CONTENT,
)
async def delete_genre(genre_id: int, db: AsyncSession = Depends(get_db)):
    stmt = select(GenreModel).where(GenreModel.id == genre_id)
    genre = await db.scalar(stmt)

    if not genre:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Genre with id {genre_id} not found.",
        )

    try:
        await db.delete(genre)
        await db.commit()
    except SQLAlchemyError:
        await db.rollback()
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Cannot delete genre because it is referenced by existing movies.",
        )


@router.post(
    "/stars",
    status_code=status.HTTP_201_CREATED,
    response_model=StarCreateResponseSchema,
)
async def create_star(
    user_data: StarCreateRequestSchema, db: AsyncSession = Depends(get_db)
):
    new_star = StarModel(**user_data.model_dump())

    db.add(new_star)
    try:
        await db.commit()
        await db.refresh(new_star)
    except SQLAlchemyError:
        await db.rollback()
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"Star with name '{user_data.name}' already exists.",
        )

    return new_star


@router.put(
    "/stars/{star_id}",
    response_model=StarUpdateResponseSchema,
)
async def update_star(
    star_id: int,
    user_data: StarUpdateRequestSchema,
    db: AsyncSession = Depends(get_db),
):
    stmt = select(StarModel).where(StarModel.id == star_id)
    star = await db.scalar(stmt)

    if not star:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Star with id {star_id} not found.",
        )

    for key, value in user_data.model_dump().items():
        setattr(star, key, value)

    try:
        await db.commit()
        await db.refresh(star)
    except SQLAlchemyError:
        await db.rollback()
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"Star with name '{user_data.name}' already exists.",
        )

    return star


@router.delete(
    "/stars/{star_id}",
    status_code=status.HTTP_204_NO_CONTENT,
)
async def delete_star(star_id: int, db: AsyncSession = Depends(get_db)):
    stmt = select(StarModel).where(StarModel.id == star_id)
    star = await db.scalar(stmt)

    if not star:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Star with id {star_id} not found.",
        )

    try:
        await db.delete(star)
        await db.commit()
    except SQLAlchemyError:
        await db.rollback()
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Cannot delete star because it is referenced by existing movies.",
        )


@router.post(
    "/directors",
    status_code=status.HTTP_201_CREATED,
    response_model=DirectorCreateResponseSchema,
)
async def create_director(
    user_data: DirectorCreateRequestSchema, db: AsyncSession = Depends(get_db)
):
    new_director = DirectorModel(**user_data.model_dump())

    db.add(new_director)
    try:
        await db.commit()
        await db.refresh(new_director)
    except SQLAlchemyError:
        await db.rollback()
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"Director with name '{user_data.name}' already exists.",
        )

    return new_director


@router.put(
    "/directors/{director_id}",
    response_model=DirectorUpdateResponseSchema,
)
async def update_director(
    director_id: int,
    user_data: DirectorUpdateRequestSchema,
    db: AsyncSession = Depends(get_db),
):
    stmt = select(DirectorModel).where(DirectorModel.id == director_id)
    director = await db.scalar(stmt)

    if not director:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Director with id {director_id} not found.",
        )

    for key, value in user_data.model_dump().items():
        setattr(director, key, value)

    try:
        await db.commit()
        await db.refresh(director)
    except SQLAlchemyError:
        await db.rollback()
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"Director with name '{user_data.name}' already exists.",
        )

    return director


@router.delete(
    "/directors/{director_id}",
    status_code=status.HTTP_204_NO_CONTENT,
)
async def delete_director(director_id: int, db: AsyncSession = Depends(get_db)):
    stmt = select(DirectorModel).where(DirectorModel.id == director_id)
    director = await db.scalar(stmt)

    if not director:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Director with id {director_id} not found.",
        )

    try:
        await db.delete(director)
        await db.commit()
    except SQLAlchemyError:
        await db.rollback()
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Cannot delete director because it is referenced by existing movies.",
        )


@router.post(
    "/certifications",
    status_code=status.HTTP_201_CREATED,
    response_model=CertificationCreateResponseSchema,
)
async def create_certification(
    user_data: CertificationCreateRequestSchema, db: AsyncSession = Depends(get_db)
):
    new_certification = CertificationModel(**user_data.model_dump())

    db.add(new_certification)
    try:
        await db.commit()
        await db.refresh(new_certification)
    except SQLAlchemyError:
        await db.rollback()
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"Certification with name '{user_data.name}' already exists.",
        )

    return new_certification


@router.put(
    "/certifications/{certification_id}",
    response_model=CertificationUpdateResponseSchema,
)
async def update_certification(
    certification_id: int,
    user_data: CertificationUpdateRequestSchema,
    db: AsyncSession = Depends(get_db),
):
    stmt = select(CertificationModel).where(CertificationModel.id == certification_id)
    certification = await db.scalar(stmt)

    if not certification:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Certification with id {certification_id} not found.",
        )

    for key, value in user_data.model_dump().items():
        setattr(certification, key, value)

    try:
        await db.commit()
        await db.refresh(certification)
    except SQLAlchemyError:
        await db.rollback()
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"Certification with name '{user_data.name}' already exists.",
        )

    return certification


@router.delete(
    "/certifications/{certification_id}",
    status_code=status.HTTP_204_NO_CONTENT,
)
async def delete_certification(
    certification_id: int, db: AsyncSession = Depends(get_db)
):
    stmt = select(CertificationModel).where(CertificationModel.id == certification_id)
    certification = await db.scalar(stmt)

    if not certification:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Certification with id {certification_id} not found.",
        )

    try:
        await db.delete(certification)
        await db.commit()
    except SQLAlchemyError:
        await db.rollback()
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Cannot delete certification because it is referenced by existing movies.",
        )


@router.post(
    "",
    status_code=status.HTTP_201_CREATED,
    response_model=MovieCreateResponseSchema,
)
async def create_movie(
    user_data: MovieCreateRequestSchema, db: AsyncSession = Depends(get_db)
):
    new_movie = MovieModel(
        **user_data.model_dump(
            exclude={
                "genre_ids",
                "director_ids",
                "star_ids",
            }
        )
    )

    stmt = select(GenreModel).where(GenreModel.id.in_(user_data.genre_ids))
    genre_results = await db.scalars(stmt)
    genres = list(genre_results.all())

    stmt = select(DirectorModel).where(DirectorModel.id.in_(user_data.director_ids))
    director_results = await db.scalars(stmt)
    directors = list(director_results.all())

    stmt = select(StarModel).where(StarModel.id.in_(user_data.star_ids))
    star_results = await db.scalars(stmt)
    stars = list(star_results.all())

    if len(genres) != len(user_data.genre_ids):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="One or more genres were not found",
        )

    if len(directors) != len(user_data.director_ids):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="One or more directors were not found",
        )

    if len(stars) != len(user_data.star_ids):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="One or more stars were not found",
        )

    new_movie.genres = genres
    new_movie.directors = directors
    new_movie.stars = stars

    db.add(new_movie)
    try:
        await db.commit()
        await db.refresh(new_movie)
    except SQLAlchemyError:
        await db.rollback()
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"Movie '{user_data.name} - {user_data.year}: {user_data.time}' already exists.",
        )

    return new_movie


@router.patch(
    "/{movie_id}",
    response_model=MovieUpdateResponseSchema,
)
async def update_movie(
    movie_id: int,
    user_data: MovieUpdateRequestSchema,
    db: AsyncSession = Depends(get_db),
):
    stmt = select(MovieModel).where(MovieModel.id == movie_id)
    movie = await db.scalar(stmt)

    if not movie:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Movie with id {movie_id} not found.",
        )

    update_data = user_data.model_dump(exclude_unset=True)

    if "genre_ids" in update_data:
        genre_ids = update_data.pop("genre_ids")
        stmt = select(GenreModel).where(GenreModel.id.in_(genre_ids))
        genre_results = await db.scalars(stmt)
        genres = list(genre_results.all())
        if len(genres) != len(genre_ids):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="One or more genres were not found",
            )
        movie.genres = genres

    if "director_ids" in update_data:
        director_ids = update_data.pop("director_ids")
        stmt = select(DirectorModel).where(DirectorModel.id.in_(director_ids))
        director_results = await db.scalars(stmt)
        directors = list(director_results.all())
        if len(directors) != len(director_ids):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="One or more directors were not found",
            )
        movie.directors = directors

    if "star_ids" in update_data:
        star_ids = update_data.pop("star_ids")
        stmt = select(StarModel).where(StarModel.id.in_(star_ids))
        star_results = await db.scalars(stmt)
        stars = list(star_results.all())
        if len(stars) != len(star_ids):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="One or more stars were not found",
            )
        movie.stars = stars

    for key, value in update_data.items():
        setattr(movie, key, value)

    try:
        await db.commit()
        await db.refresh(movie)
    except SQLAlchemyError:
        await db.rollback()
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"Movie '{movie.name} - {movie.year}: {movie.time}' already exists.",
        )

    return movie


@router.delete(
    "/{movie_id}",
    status_code=status.HTTP_204_NO_CONTENT,
)
async def delete_movie(movie_id: int, db: AsyncSession = Depends(get_db)):
    stmt = select(MovieModel).where(MovieModel.id == movie_id)
    movie = await db.scalar(stmt)

    if not movie:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Movie with id {movie_id} not found.",
        )

    stmt = select(
        exists()
        .select_from(PaymentItemModel)
        .join(PaymentModel, PaymentItemModel.payment_id == PaymentModel.id)
        .where(
            PaymentItemModel.movie_id == movie_id,
            PaymentModel.status == PaymentStatusEnum.SUCCESSFUL,
        )
    )
    has_purchases = await db.scalar(stmt)

    if has_purchases:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Cannot delete movie as it has already been purchased by users.",
        )

    try:
        await db.delete(movie)
        await db.commit()
    except SQLAlchemyError:
        await db.rollback()
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Failed to delete movie.",
        )

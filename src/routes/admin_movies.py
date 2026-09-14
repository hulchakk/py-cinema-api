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
    summary="Create a new genre",
    description="Creates a new genre record in the database.",
    responses={
        status.HTTP_201_CREATED: {
            "model": GenreCreateResponseSchema,
            "description": "Genre successfully created.",
        },
        status.HTTP_409_CONFLICT: {
            "description": "Conflict: Genre with this name already exists.",
            "content": {
                "application/json": {
                    "example": {"detail": "Genre with name 'Action' already exists."}
                }
            },
        },
    },
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
    summary="Update an existing genre",
    description="Updates the details of a specific genre by its ID.",
    responses={
        status.HTTP_200_OK: {
            "model": GenreUpdateResponseSchema,
            "description": "Genre successfully updated.",
        },
        status.HTTP_404_NOT_FOUND: {
            "description": "Genre not found.",
            "content": {
                "application/json": {
                    "example": {"detail": "Genre with id 1 not found."}
                }
            },
        },
        status.HTTP_409_CONFLICT: {
            "description": "Conflict: Another genre with the target name already exists.",
            "content": {
                "application/json": {
                    "example": {"detail": "Genre with name 'Action' already exists."}
                }
            },
        },
    },
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
    summary="Delete a genre",
    description="Deletes a genre by its ID if it is not linked to any existing movies.",
    responses={
        status.HTTP_204_NO_CONTENT: {
            "description": "Genre successfully deleted.",
        },
        status.HTTP_400_BAD_REQUEST: {
            "description": "Cannot delete genre due to active references in movies.",
            "content": {
                "application/json": {
                    "example": {
                        "detail": "Cannot delete genre because it is referenced by existing movies."
                    }
                }
            },
        },
        status.HTTP_404_NOT_FOUND: {
            "description": "Genre not found.",
            "content": {
                "application/json": {
                    "example": {"detail": "Genre with id 1 not found."}
                }
            },
        },
    },
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
    summary="Create a new star",
    description="Creates a new movie star (actor) record in the database.",
    responses={
        status.HTTP_201_CREATED: {
            "model": StarCreateResponseSchema,
            "description": "Star successfully created.",
        },
        status.HTTP_409_CONFLICT: {
            "description": "Conflict: Star with this name already exists.",
            "content": {
                "application/json": {
                    "example": {
                        "detail": "Star with name 'Keanu Reeves' already exists."
                    }
                }
            },
        },
    },
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
    summary="Update an existing star",
    description="Updates details for an existing star by their ID.",
    responses={
        status.HTTP_200_OK: {
            "model": StarUpdateResponseSchema,
            "description": "Star successfully updated.",
        },
        status.HTTP_404_NOT_FOUND: {
            "description": "Star not found.",
            "content": {
                "application/json": {"example": {"detail": "Star with id 1 not found."}}
            },
        },
        status.HTTP_409_CONFLICT: {
            "description": "Conflict: Star with this name already exists.",
            "content": {
                "application/json": {
                    "example": {
                        "detail": "Star with name 'Keanu Reeves' already exists."
                    }
                }
            },
        },
    },
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
    summary="Delete a star",
    description="Deletes a star by ID if not associated with any movies.",
    responses={
        status.HTTP_204_NO_CONTENT: {
            "description": "Star successfully deleted.",
        },
        status.HTTP_400_BAD_REQUEST: {
            "description": "Cannot delete star because it is referenced by existing movies.",
            "content": {
                "application/json": {
                    "example": {
                        "detail": "Cannot delete star because it is referenced by existing movies."
                    }
                }
            },
        },
        status.HTTP_404_NOT_FOUND: {
            "description": "Star not found.",
            "content": {
                "application/json": {"example": {"detail": "Star with id 1 not found."}}
            },
        },
    },
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
    summary="Create a new director",
    description="Creates a new movie director entry.",
    responses={
        status.HTTP_201_CREATED: {
            "model": DirectorCreateResponseSchema,
            "description": "Director successfully created.",
        },
        status.HTTP_409_CONFLICT: {
            "description": "Conflict: Director with this name already exists.",
            "content": {
                "application/json": {
                    "example": {
                        "detail": "Director with name 'Christopher Nolan' already exists."
                    }
                }
            },
        },
    },
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
    summary="Update an existing director",
    description="Updates information for a specific director by their ID.",
    responses={
        status.HTTP_200_OK: {
            "model": DirectorUpdateResponseSchema,
            "description": "Director successfully updated.",
        },
        status.HTTP_404_NOT_FOUND: {
            "description": "Director not found.",
            "content": {
                "application/json": {
                    "example": {"detail": "Director with id 1 not found."}
                }
            },
        },
        status.HTTP_409_CONFLICT: {
            "description": "Conflict: Director with this name already exists.",
            "content": {
                "application/json": {
                    "example": {
                        "detail": "Director with name 'Christopher Nolan' already exists."
                    }
                }
            },
        },
    },
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
    summary="Delete a director",
    description="Deletes a director by ID if they have no movies assigned.",
    responses={
        status.HTTP_204_NO_CONTENT: {
            "description": "Director successfully deleted.",
        },
        status.HTTP_400_BAD_REQUEST: {
            "description": "Cannot delete director because they are referenced by existing movies.",
            "content": {
                "application/json": {
                    "example": {
                        "detail": "Cannot delete director because it is referenced by existing movies."
                    }
                }
            },
        },
        status.HTTP_404_NOT_FOUND: {
            "description": "Director not found.",
            "content": {
                "application/json": {
                    "example": {"detail": "Director with id 1 not found."}
                }
            },
        },
    },
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
    summary="Create a new certification",
    description="Creates a new certification classification (e.g., PG-13, R) for movies.",
    responses={
        status.HTTP_201_CREATED: {
            "model": CertificationCreateResponseSchema,
            "description": "Certification successfully created.",
        },
        status.HTTP_409_CONFLICT: {
            "description": "Conflict: Certification with this name already exists.",
            "content": {
                "application/json": {
                    "example": {
                        "detail": "Certification with name 'PG-13' already exists."
                    }
                }
            },
        },
    },
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
    summary="Update an existing certification",
    description="Updates an existing certification by its ID.",
    responses={
        status.HTTP_200_OK: {
            "model": CertificationUpdateResponseSchema,
            "description": "Certification successfully updated.",
        },
        status.HTTP_404_NOT_FOUND: {
            "description": "Certification not found.",
            "content": {
                "application/json": {
                    "example": {"detail": "Certification with id 1 not found."}
                }
            },
        },
        status.HTTP_409_CONFLICT: {
            "description": "Conflict: Certification with this name already exists.",
            "content": {
                "application/json": {
                    "example": {
                        "detail": "Certification with name 'PG-13' already exists."
                    }
                }
            },
        },
    },
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
    summary="Delete a certification",
    description="Deletes a certification by ID if not assigned to any existing movies.",
    responses={
        status.HTTP_204_NO_CONTENT: {
            "description": "Certification successfully deleted.",
        },
        status.HTTP_400_BAD_REQUEST: {
            "description": "Cannot delete certification because it is referenced by existing movies.",
            "content": {
                "application/json": {
                    "example": {
                        "detail": "Cannot delete certification because it is referenced by existing movies."
                    }
                }
            },
        },
        status.HTTP_404_NOT_FOUND: {
            "description": "Certification not found.",
            "content": {
                "application/json": {
                    "example": {"detail": "Certification with id 1 not found."}
                }
            },
        },
    },
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
    summary="Create a new movie",
    description="Creates a movie record with relations to genres, directors, and stars. All specified relation IDs must exist in the database.",
    responses={
        status.HTTP_201_CREATED: {
            "model": MovieCreateResponseSchema,
            "description": "Movie successfully created.",
        },
        status.HTTP_400_BAD_REQUEST: {
            "description": "Bad Request: One or more provided relation IDs (genres, directors, stars) do not exist.",
            "content": {
                "application/json": {
                    "examples": {
                        "missing_genres": {
                            "value": {"detail": "One or more genres were not found"}
                        },
                        "missing_directors": {
                            "value": {"detail": "One or more directors were not found"}
                        },
                        "missing_stars": {
                            "value": {"detail": "One or more stars were not found"}
                        },
                    }
                }
            },
        },
        status.HTTP_409_CONFLICT: {
            "description": "Conflict: Movie with the same name, year, and runtime duration already exists.",
            "content": {
                "application/json": {
                    "example": {
                        "detail": "Movie 'Inception - 2010: 148' already exists."
                    }
                }
            },
        },
    },
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
    summary="Partially update a movie",
    description="Updates specific fields of a movie by ID, including updating relations to genres, directors, and stars if provided.",
    responses={
        status.HTTP_200_OK: {
            "model": MovieUpdateResponseSchema,
            "description": "Movie successfully updated.",
        },
        status.HTTP_400_BAD_REQUEST: {
            "description": "Bad Request: One or more updated relation IDs (genres, directors, stars) do not exist.",
            "content": {
                "application/json": {
                    "examples": {
                        "missing_genres": {
                            "value": {"detail": "One or more genres were not found"}
                        },
                        "missing_directors": {
                            "value": {"detail": "One or more directors were not found"}
                        },
                        "missing_stars": {
                            "value": {"detail": "One or more stars were not found"}
                        },
                    }
                }
            },
        },
        status.HTTP_404_NOT_FOUND: {
            "description": "Movie not found.",
            "content": {
                "application/json": {
                    "example": {"detail": "Movie with id 1 not found."}
                }
            },
        },
        status.HTTP_409_CONFLICT: {
            "description": "Conflict: Updated properties result in a duplicate movie entry.",
            "content": {
                "application/json": {
                    "example": {
                        "detail": "Movie 'Inception - 2010: 148' already exists."
                    }
                }
            },
        },
    },
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
    summary="Delete a movie",
    description="Deletes a movie by ID. Returns an error if the movie has already been purchased successfully by any user.",
    responses={
        status.HTTP_204_NO_CONTENT: {
            "description": "Movie successfully deleted.",
        },
        status.HTTP_400_BAD_REQUEST: {
            "description": "Failed to delete movie due to a database exception.",
            "content": {
                "application/json": {"example": {"detail": "Failed to delete movie."}}
            },
        },
        status.HTTP_404_NOT_FOUND: {
            "description": "Movie not found.",
            "content": {
                "application/json": {
                    "example": {"detail": "Movie with id 1 not found."}
                }
            },
        },
        status.HTTP_409_CONFLICT: {
            "description": "Conflict: Cannot delete movie as it has associated successful purchase payments.",
            "content": {
                "application/json": {
                    "example": {
                        "detail": "Cannot delete movie as it has already been purchased by users."
                    }
                }
            },
        },
    },
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

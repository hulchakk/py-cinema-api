from fastapi import FastAPI
from fastapi.params import Depends

from routes import (
    accounts,
    admin_movies,
    movies,
)
from security.dependencies import allow_staff

app = FastAPI()

app.include_router(
    accounts.router,
    prefix="/api/v1",
    tags=["User: accounts"],
)
app.include_router(
    movies.router,
    prefix="/api/v1",
    tags=["User: movies"],
)
app.include_router(
    admin_movies.router,
    prefix="/api/v1",
    tags=["Admin: movies"],
    dependencies=[Depends(allow_staff)],
)

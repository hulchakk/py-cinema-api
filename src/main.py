from fastapi import FastAPI
from fastapi.params import Depends

from routes import (
    accounts,
    admin_movies,
    movies,
    carts,
    orders,
    payments,
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
app.include_router(
    carts.router,
    prefix="/api/v1",
    tags=["User: carts"],
)
app.include_router(
    orders.router,
    prefix="/api/v1",
    tags=["User: orders"],
)
app.include_router(
    payments.router,
    prefix="/api/v1",
    tags=["User: payments"],
)

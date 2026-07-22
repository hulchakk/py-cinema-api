from fastapi import FastAPI

from routes import accounts

app = FastAPI()

app.include_router(
    accounts.router,
    prefix="/api/v1",
    tags=["accounts"],
)

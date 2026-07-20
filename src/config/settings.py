import os

from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    DB_URL: str = os.getenv("DATABASE_URL", "sqlite:///db.sqlite3")

    class Config:
        env_file = ".env"


settings = Settings()

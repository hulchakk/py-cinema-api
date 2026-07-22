import os

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    DB_URL: str = "sqlite+aiosqlite:///db.sqlite3"

    SECRET_KEY_ACCESS: str = "super-secret-access-key-change-me"
    SECRET_KEY_REFRESH: str = "super-secret-refresh-key-change-me"
    JWT_SIGNING_ALGORITHM: str = "HS256"

    LOGIN_TIME_DAYS: int = 86400

    model_config = SettingsConfigDict(
        env_file=".env", env_file_encoding="utf-8", extra="ignore"
    )


settings = Settings()

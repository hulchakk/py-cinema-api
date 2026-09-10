import os

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    DB_URL: str = "sqlite+aiosqlite:///db.sqlite3"

    SECRET_KEY_ACCESS: str = "super-secret-access-key-change-me"
    SECRET_KEY_REFRESH: str = "super-secret-refresh-key-change-me"
    JWT_SIGNING_ALGORITHM: str = "HS256"

    LOGIN_TIME_DAYS: int = 86400

    STRIPE_SECRET_KEY: str = "sk_test_change_me_in_env"
    STRIPE_WEBHOOK_SECRET: str = "whsec_change_me_in_env"

    S3_STORAGE_HOST: str = "minio-cinema"
    S3_STORAGE_PORT: int = 9000
    S3_STORAGE_ACCESS_KEY: str = "minio_admin"
    S3_STORAGE_SECRET_KEY: str = "some_password"
    S3_BUCKET_NAME: str = "cinema-storage"

    @property
    def S3_STORAGE_ENDPOINT(self) -> str:
        return f"http://{self.S3_STORAGE_HOST}:{self.S3_STORAGE_PORT}"

    model_config = SettingsConfigDict(
        env_file=".env", env_file_encoding="utf-8", extra="ignore"
    )


settings = Settings()

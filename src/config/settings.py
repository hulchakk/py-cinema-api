import os
from pathlib import Path

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    BASE_DIR: Path = Path(__file__).parent.parent
    DB_URL: str = "sqlite+aiosqlite:///db.sqlite3"

    SECRET_KEY_ACCESS: str = "super-secret-access-key-change-me"
    SECRET_KEY_REFRESH: str = "super-secret-refresh-key-change-me"
    JWT_SIGNING_ALGORITHM: str = "HS256"

    LOGIN_TIME_DAYS: int = 86400

    PATH_TO_EMAIL_TEMPLATES_DIR: str = str(BASE_DIR / "notifications" / "templates")
    ACTIVATION_EMAIL_TEMPLATE_NAME: str = "activation_email.html"
    ACTIVATION_COMPLETE_EMAIL_TEMPLATE_NAME: str = "activation_complete_email.html"
    PASSWORD_RESET_TEMPLATE_NAME: str = "password_reset_email.html"
    PASSWORD_RESET_COMPLETE_TEMPLATE_NAME: str = "password_reset_complete_email.html"
    ORDER_CONFIRMATION_EMAIL_TEMPLATE_NAME: str = "order_confirmation.html"
    PAYMENT_RECEIPT_EMAIL_TEMPLATE_NAME: str = "payment_receipt.html"

    EMAIL_HOST: str = "host"
    EMAIL_PORT: int = int(25)
    EMAIL_HOST_USER: str = "test_user"
    EMAIL_HOST_PASSWORD: str = "test_password"
    EMAIL_USE_TLS: bool = False
    MAILHOG_API_PORT: int = 8025

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

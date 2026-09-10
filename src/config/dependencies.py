from fastapi import Depends

from config.settings import settings, Settings
from security.interfaces import JWTAuthManagerInterface
from security.token_manager import JWTAuthManager
from services.storages.interfaces import S3StorageInterface
from services.storages.s3 import S3StorageClient


def get_settings() -> Settings:
    return settings


def get_jwt_auth_manager(
    settings: Settings = Depends(get_settings),
) -> JWTAuthManagerInterface:
    return JWTAuthManager(
        secret_key_access=settings.SECRET_KEY_ACCESS,
        secret_key_refresh=settings.SECRET_KEY_REFRESH,
        algorithm=settings.JWT_SIGNING_ALGORITHM,
    )


def get_s3_storage_client(
    settings: Settings = Depends(get_settings),
) -> S3StorageInterface:

    return S3StorageClient(
        endpoint_url=settings.S3_STORAGE_ENDPOINT,
        access_key=settings.S3_STORAGE_ACCESS_KEY,
        secret_key=settings.S3_STORAGE_SECRET_KEY,
        bucket_name=settings.S3_BUCKET_NAME,
    )

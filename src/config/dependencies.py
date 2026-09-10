from fastapi import Depends

from config.settings import settings, Settings
from security.interfaces import JWTAuthManagerInterface
from security.token_manager import JWTAuthManager
from services.notifications.emails import EmailSender
from services.notifications.interfaces import EmailSenderInterface
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


def get_accounts_email_notificator(
    settings: Settings = Depends(get_settings)
) -> EmailSenderInterface:
    return EmailSender(
        hostname=settings.EMAIL_HOST,
        port=settings.EMAIL_PORT,
        email=settings.EMAIL_HOST_USER,
        password=settings.EMAIL_HOST_PASSWORD,
        use_tls=settings.EMAIL_USE_TLS,
        template_dir=settings.PATH_TO_EMAIL_TEMPLATES_DIR,
        activation_email_template_name=settings.ACTIVATION_EMAIL_TEMPLATE_NAME,
        activation_complete_email_template_name=settings.ACTIVATION_COMPLETE_EMAIL_TEMPLATE_NAME,
        password_email_template_name=settings.PASSWORD_RESET_TEMPLATE_NAME,
        password_complete_email_template_name=settings.PASSWORD_RESET_COMPLETE_TEMPLATE_NAME,
        order_confirmation_email_template_name=settings.ORDER_CONFIRMATION_EMAIL_TEMPLATE_NAME,
        payment_receipt_email_template_name=settings.PAYMENT_RECEIPT_EMAIL_TEMPLATE_NAME,
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

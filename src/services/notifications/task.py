import asyncio
from datetime import datetime, timezone
from sqlalchemy import select
from sqlalchemy.orm import selectinload

from config.celery_config import celery_app
from database.models.accounts import ActivationTokenModel
from database.session import SessionLocal
from services.notifications.emails import EmailSender
from config.settings import settings


def run_async(coro):
    return asyncio.get_event_loop().run_until_complete(coro)


@celery_app.task
def process_expired_activation_tokens():
    run_async(_process_expired_tokens_logic())


async def _process_expired_tokens_logic():
    async with SessionLocal() as db:
        now = datetime.now(timezone.utc)

        stmt = (
            select(ActivationTokenModel)
            .where(ActivationTokenModel.expires_at <= now)
            .options(selectinload(ActivationTokenModel.user))
        )
        expired_tokens = (await db.scalars(stmt)).all()

        if not expired_tokens:
            return

        email_sender = EmailSender(
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

        for token_record in expired_tokens:
            user = token_record.user

            if user and not user.is_active:
                await db.delete(token_record)
                await db.flush()

                new_token = ActivationTokenModel(user_id=user.id)
                db.add(new_token)
                await db.flush()

                activation_link = f"{settings.FRONTEND_URL}/activate?email={user.email}&token={new_token.token}"
                await email_sender.send_activation_email(
                    email=user.email,
                    activation_link=activation_link,
                )
            else:
                await db.delete(token_record)

        await db.commit()

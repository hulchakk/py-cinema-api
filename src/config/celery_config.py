from celery import Celery
from config.settings import settings
from celery.schedules import crontab

celery_app = Celery(
    "online_cinema",
    broker=settings.REDIS_URL,
    backend=settings.REDIS_URL,
)

celery_app.conf.update(
    task_serializer="json",
    accept_content=["json"],
    result_serializer="json",
    timezone="UTC",
    enable_utc=True,
    imports=["services.notifications.task"],
)

celery_app.conf.beat_schedule = {
    "process-expired-tokens-every-hour": {
        "task": "services.notifications.task.process_expired_activation_tokens",
        "schedule": crontab(minute=0, hour="*"),
    },
}

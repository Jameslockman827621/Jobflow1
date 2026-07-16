from celery import Celery
from app.core.config import settings
from .scheduler import beat_schedule

celery_app = Celery(
    "jobscale",
    broker=settings.REDIS_URL,
    backend=settings.REDIS_URL,
    include=[
        "app.tasks.jobs",
        "app.tasks.applications",
        "app.tasks.notifications",
        "app.tasks.alerts",
        "app.tasks.on_demand_search",
        "app.tasks.monitoring",
        "app.tasks.headless_apply_tasks",
        "app.tasks.apify_scraper",
        "app.tasks.deduplication",
    ],
)

celery_app.conf.update(
    task_serializer="json",
    accept_content=["json"],
    result_serializer="json",
    timezone="UTC",
    enable_utc=True,
    task_track_started=True,
    task_time_limit=300,  # 5 minute max per task
    worker_prefetch_multiplier=1,
    task_acks_late=True,
    task_default_rate_limit="30/m",
    beat_schedule=beat_schedule,
)

"""Celery app entrypoint for worker/beat (`celery -A app.tasks.celery_app`)."""

from app.tasks import celery_app  # noqa: F401

__all__ = ["celery_app"]

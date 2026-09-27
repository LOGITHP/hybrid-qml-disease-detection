"""Celery asynchronous task queue application configuration."""

import os
from celery import Celery
from app.core.config import settings

redis_url = os.getenv("REDIS_URL", settings.REDIS_URL)

celery_app = Celery(
    "hybrid_qml_tasks",
    broker=redis_url,
    backend=redis_url,
    include=["app.workers.tasks"],
)

celery_app.conf.update(
    task_serializer="json",
    accept_content=["json"],
    result_serializer="json",
    timezone="UTC",
    enable_utc=True,
    task_track_started=True,
    task_time_limit=3600,  # 1 hour maximum per training or QPU task
)

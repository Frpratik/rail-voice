from celery import Celery

from app.core.config import settings

# When CELERY_ENABLED=false (free tier), use in-process memory broker so imports stay safe.
_broker = settings.celery_broker_url or "memory://"
_backend = settings.celery_result_backend or "cache+memory://"

celery_app = Celery(
    "railvoice",
    broker=_broker,
    backend=_backend,
)

celery_app.conf.update(
    task_serializer="json",
    accept_content=["json"],
    result_serializer="json",
    timezone="Asia/Kolkata",
    enable_utc=True,
    task_always_eager=not settings.celery_enabled,
    task_eager_propagates=True,
    task_queues={
        "high": {"exchange": "high", "routing_key": "high"},
        "default": {"exchange": "default", "routing_key": "default"},
        "low": {"exchange": "low", "routing_key": "low"},
    },
    task_default_queue="default",
    beat_schedule={
        "recalc-priority-scores": {
            "task": "app.workers.tasks.recalc_priority_scores",
            "schedule": 900.0,
        },
        "recalc-trending-scores": {
            "task": "app.workers.tasks.recalc_trending_scores",
            "schedule": 900.0,
        },
        "check-sla-breaches": {
            "task": "app.workers.tasks.check_sla_breaches",
            "schedule": 1800.0,
        },
        "daily-ai-summary": {
            "task": "app.workers.tasks.generate_daily_ai_summary",
            "schedule": 86400.0,
        },
    }
    if settings.celery_enabled
    else {},
)

celery_app.autodiscover_tasks(["app.workers"])

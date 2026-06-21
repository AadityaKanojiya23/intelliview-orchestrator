"""
Celery Application Setup
Initializes Celery and connects to Redis message broker
"""

from celery import Celery
from config import REDIS_URL

# Initialize Celery app
celery_app = Celery("interview_tasks", broker=REDIS_URL, backend=REDIS_URL)

# Configure Celery settings
celery_app.conf.update(
    task_serializer="json",
    accept_content=["json"],
    result_serializer="json",
    timezone="UTC",
    enable_utc=True,
    task_track_started=True,
    task_time_limit=30 * 60,  # 30 minutes hard limit
    task_soft_time_limit=25 * 60,  # 25 minutes soft limit
)

# Auto-discover tasks from workers module
celery_app.autodiscover_tasks(["workers"])

if __name__ == "__main__":
    celery_app.start()

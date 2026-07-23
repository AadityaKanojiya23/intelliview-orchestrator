"""Celery Application Setup.

Initialises Celery with the Redis broker, sensible reliability defaults,
and a `session_failed` signal that lets us mark the DB session as
FAILED only after Celery has exhausted its retries (rather than on
every transient exception).
"""
"""
# TODO:
 Separate worker deployment is pending.
 These queues prepare task routing for future deployment where:
 - interview queue will be processed by workers with
   worker_prefetch_multiplier=1 for long-running tasks.
 - maintenance queue will be processed by dedicated workers with a
   higher worker_prefetch_multiplier for short-running tasks.

from celery import Celery, signals
from kombu import Queue

"""
from celery import Celery, signals
from kombu import Queue
from config import REDIS_URL



celery_app = Celery("interview_tasks", broker=REDIS_URL, backend=REDIS_URL)

# --- Priority queues -------------------------------------------------------
# Two physical queues. Workers dedicated to "high-priority" (see the
# `celery worker -Q high-priority` command in the deployment docs/README)
# guarantee that high-priority work is never stuck behind default work,
# rather than relying on ordering within a single queue.
HIGH_PRIORITY_QUEUE = "high-priority"
DEFAULT_QUEUE = "default"


def route_by_priority(name, args, kwargs, options, task=None, **_extra):
    """Celery task router — called for every task right before it's
    published, and decides which queue it should land in.

    Priority is set by the API layer (`main.py`'s `/start-interview`
    endpoint) when a session is queued: it's stored in the session's
    cached data via `SessionManager.update_session_status(..., metadata=
    {"priority": priority.name})`. Stored values are uppercase enum names
    — "HIGH", "MEDIUM", "LOW" (see `orchestrator.scheduler.TaskPriority`).

    We fetch it via the existing `SessionManager().get_session(session_id)`
    — no new orchestrator method needed. Any failure to resolve a priority
    (missing session, orchestrator unreachable, unrecognized value) falls
    back to the default queue rather than raising, so a broken lookup
    never blocks task dispatch.
    """
    if options.get("queue"):
        return {}  # caller already picked a queue explicitly, leave it alone

    session_id = args[0] if args else kwargs.get("session_id")
    if session_id is None:
        return {"queue": DEFAULT_QUEUE}

    try:
        # Imported lazily so importing this module doesn't pull in the
        # DB/orchestrator stack before the worker process is ready.
        from orchestrator.session_manager import SessionManager

        session_data = SessionManager().get_session(session_id)
        priority = (session_data or {}).get("priority", "")
    except Exception as exc:
        import logging

        logging.getLogger(__name__).warning(
            "Priority lookup failed for session %s, falling back to default queue: %s",
            session_id,
            exc,
        )
        return {"queue": DEFAULT_QUEUE}

    return {"queue": HIGH_PRIORITY_QUEUE if str(priority).upper() == "HIGH" else DEFAULT_QUEUE}


celery_app.conf.update(
    task_serializer="json",
    accept_content=["json"],
    result_serializer="json",
    timezone="UTC",
    enable_utc=True,
    task_track_started=True,
    task_time_limit=30 * 60,
    task_soft_time_limit=25 * 60,
    task_acks_late=True,
    task_reject_on_worker_lost=True,

    # Long-running interview tasks should reserve only one task at a time
    worker_prefetch_multiplier=1,

    broker_connection_retry_on_startup=True,
    task_queues=(   # Priority queues + routing
        Queue(HIGH_PRIORITY_QUEUE),
        Queue(DEFAULT_QUEUE),
    ),
    task_default_queue=DEFAULT_QUEUE,
    task_routes=(route_by_priority,),
    # Periodic beat schedule — scan for due retries every 60 seconds
    beat_schedule={
        "scan-due-retries": {
            "task": "workers.tasks.scan_and_dispatch_retries",
            "schedule": 60.0,
        },
    },
)

# Auto-discover tasks from workers module
celery_app.autodiscover_tasks(["workers"])


@signals.task_failure.connect
def _on_task_failure(task_id, exception, args, kwargs, traceback, einfo, **_extra):
    """When a task fails permanently (retries exhausted), mark the
    session as FAILED so the dashboard reflects reality.

    `args[0]` is the session_id passed to `process_interview_session`.
    Imported lazily so importing this module doesn't pull in the DB stack
    before the worker process is ready.
    """
    try:
        from orchestrator.session_manager import SessionManager

        session_id = args[0] if args else None
        if not session_id:
            return
        SessionManager().mark_session_failed(session_id, f"Celery task exhausted retries: {exception!s}")
    except Exception as exc:
        # Don't let a signal handler crash the worker.
        import logging

        logging.getLogger(__name__).warning("task_failure handler failed: %s", exc)


if __name__ == "__main__":
    celery_app.start()
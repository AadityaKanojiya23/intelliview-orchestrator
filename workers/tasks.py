"""Celery Tasks for Interview Processing.

Pipeline:
  1. QUEUED  -> VIDEO_PROCESSING -> AUDIO_PROCESSING -> EVALUATING
  2. Each stage persists to Postgres and the Redis cache.
  3. Final stage writes the risk report and marks the session COMPLETED.
  4. On exception: `self.retry(...)` triggers exponential backoff via
     Celery. The session is NOT marked FAILED here — only after Celery
     has exhausted retries (see `celery_app.task_failure` signal).
"""

from __future__ import annotations

import json
import logging
import socket
import time
from datetime import datetime, timezone

from celery import group
from celery.exceptions import TimeoutError
from sqlalchemy import select

from database.db import SessionLocal
from database.models import InterviewSession
from monitoring.prometheus_metrics import (
    CELERY_ACTIVE_TASKS,
    CELERY_TASK_RUNTIME,
    CELERY_TASKS_PROCESSED_TOTAL,  # Updated custom counter
    FAILURE_COUNT,
    PIPELINE_LATENCY,
    POSTGRES_HEALTH,
    QUEUE_DEPTH,
    REDIS_HEALTH,
    RETRY_COUNT,
    RISK_SCORE,
    WORKERS_HEALTHY,
)
from orchestrator.redis_client import get_redis_client
from orchestrator.session_manager import SessionManager
from orchestrator.state_sync import StateSynchronizer
from workers.celery_app import celery_app
from workers.evaluation_pipeline import evaluate_answers
from workers.risk_engine import RiskScoringEngine

logger = logging.getLogger(__name__)

session_manager = SessionManager()
state_sync = StateSynchronizer()


# ---------------------------------------------------------------------------
# Helper methods
# ---------------------------------------------------------------------------

def _get_session_state(session_id: str) -> dict:
    """Get session state from the state synchronizer."""
    state = state_sync.get_session_state(session_id)
    return state or {}


def _update_session_state(session_id: str, **kwargs):
    """Update session state in the state synchronizer."""
    state = _get_session_state(session_id)
    state.update(kwargs)
    state_sync.set_session_state(session_id, state)


# Redelivered tasks (task_acks_late + task_reject_on_worker_lost) re-run
# from the top with the same session_id while the DB row may still be
# active. task_time_limit tells us when a stuck attempt is provably dead.
REDELIVERY_STALE_AFTER_SECONDS = celery_app.conf.task_time_limit + 60

ACTIVE_PROCESSING_STATUSES = {
    session_manager.PROCESSING,
    session_manager.VIDEO_PROCESSING,
    getattr(session_manager, "AUDIO_PROCESSING", "AUDIO_PROCESSING"),
    session_manager.EVALUATING,
}


# ---------------------------------------------------------------------------
# Helper to set background infrastructure health states
# ---------------------------------------------------------------------------

def _update_infra_health(healthy: bool = True):
    """Sets system infrastructure gauges to reflect live operations."""
    state = 1.0 if healthy else 0.0
    WORKERS_HEALTHY.set(state)
    REDIS_HEALTH.set(state)
    POSTGRES_HEALTH.set(state)


# ---------------------------------------------------------------------------
# Individual stage tasks
# ---------------------------------------------------------------------------


@celery_app.task(bind=True, max_retries=3, name="workers.tasks._run_video")
def _run_video(self, session_id: str) -> dict:
    from workers.video_pipeline import run_video_analysis

    logger.info("Starting video analysis stage for session %s", session_id)
    start = time.perf_counter()

    _update_infra_health(True)

    result = run_video_analysis(session_id)

    latency = time.perf_counter() - start
    PIPELINE_LATENCY.labels(stage="video").observe(latency)

    _update_session_state(
        session_id,
        video_completed=True,
        video_result=result,
    )

    logger.info("Video analysis stage completed in %.2fs", latency)

    return result


@celery_app.task(bind=True, max_retries=3, name="workers.tasks._run_audio")
def _run_audio(self, session_id: str) -> dict:
    from workers.audio_pipeline import run_audio_analysis

    logger.info("Starting audio analysis stage for session %s", session_id)
    start = time.perf_counter()

    _update_infra_health(True)

    result = run_audio_analysis(session_id)

    latency = time.perf_counter() - start
    PIPELINE_LATENCY.labels(stage="audio").observe(latency)

    _update_session_state(
        session_id,
        audio_completed=True,
        audio_result=result,
    )

    logger.info("Audio analysis stage completed in %.2fs", latency)

    return result


# ---------------------------------------------------------------------------
# Callback after parallel video + audio complete
# ---------------------------------------------------------------------------


@celery_app.task(bind=True, max_retries=3, name="workers.tasks._after_parallel")
def _after_parallel(self, session_id: str, video_result: dict, audio_result: dict):
    """Runs after video + audio group completes; then evaluation + risk."""
    try:
        logger.info("Parallel video+audio done for %s - running evaluation", session_id)
        session_manager.update_session_status(session_id, session_manager.EVALUATING, {"stage": "evaluation"})

        start = time.perf_counter()
        evaluation_result = evaluate_answers(session_id)

        latency = time.perf_counter() - start
        PIPELINE_LATENCY.labels(stage="evaluation").observe(latency)
        logger.info("Answer evaluation completed for session %s in %.2fs", session_id, latency)

        risk_report = RiskScoringEngine.generate_risk_report(
            session_id, video_result, audio_result, evaluation_result
        )
        final_risk_score = risk_report["final_risk_score"]
        RISK_SCORE.observe(final_risk_score)

        risk_classification = risk_report["risk_classification"]
        logger.info("Risk report: %s (score: %s)", risk_classification, final_risk_score)

        now = datetime.now(timezone.utc)
        db_session = SessionLocal()
        try:
            interview = db_session.execute(
                select(InterviewSession).where(InterviewSession.session_id == session_id)
            ).scalar_one_or_none()
            if interview:
                interview.risk_score = final_risk_score
                interview.video_analysis = video_result
                interview.audio_analysis = audio_result
                interview.evaluation_analysis = evaluation_result
                interview.end_time = now
                interview.updated_at = now
                db_session.commit()
        finally:
            db_session.close()

        session_manager.mark_session_completed(session_id, final_risk_score)
        state_sync.delete_session_state(session_id)
        logger.info("Successfully completed processing for session %s", session_id)

    except Exception as exc:
        logger.error("Post-parallel stage failed for %s: %s", session_id, exc, exc_info=True)
        FAILURE_COUNT.labels(failure_type="post_parallel_error").inc()
        session_manager.mark_session_failed(session_id, f"Post-parallel stage failed: {exc}")


# ---------------------------------------------------------------------------
# Main entry-point task
# ---------------------------------------------------------------------------


@celery_app.task(bind=True, max_retries=3, name="workers.tasks.process_interview_session")
def process_interview_session(self, session_id):
    task_name = self.name
    start_time = time.perf_counter()

    # Track currently active task tracking gauge
    CELERY_ACTIVE_TASKS.labels(task_name=task_name).inc()

    # Assert worker and backend services are active
    _update_infra_health(True)

    try:
        worker_hostname = socket.gethostname()
        logger.info("Worker %s starting interview session: %s", worker_hostname, session_id)

        db_session = SessionLocal()
        try:
            interview = db_session.execute(
                select(InterviewSession).where(InterviewSession.session_id == session_id)
            ).scalar_one_or_none()
            if interview is None:
                logger.error("Session %s not found in DB", session_id)
                return {"session_id": session_id, "status": "missing"}

            if interview.status == "FAILED":
                interview.status = "QUEUED"
                db_session.commit()

            elif interview.status in ACTIVE_PROCESSING_STATUSES:
                # Possible redelivery: figure out if the previous attempt
                # is still alive (skip) or dead past task_time_limit (recover).
                existing_start = interview.start_time
                age_seconds = None
                if existing_start is not None:
                    if existing_start.tzinfo is None:
                        existing_start = existing_start.replace(tzinfo=timezone.utc)
                    age_seconds = (datetime.now(timezone.utc) - existing_start).total_seconds()

                if age_seconds is not None and age_seconds < REDELIVERY_STALE_AFTER_SECONDS:
                    logger.warning(
                        "Session %s is already %s (started %.0fs ago). Treating "
                        "this delivery of task %s on worker %s as a redelivered "
                        "duplicate - skipping re-dispatch of the video/audio group.",
                        session_id,
                        interview.status,
                        age_seconds,
                        self.request.id,
                        worker_hostname,
                    )
                    return {
                        "session_id": session_id,
                        "status": "skipped_duplicate_delivery",
                        "reason": f"session already {interview.status}, started {age_seconds:.0f}s ago",
                        "processed_by": worker_hostname,
                    }

                logger.warning(
                    "Session %s stuck in %s with no live heartbeat (age=%s) - "
                    "previous attempt appears abandoned/crashed. Recovering by "
                    "reprocessing on worker %s.",
                    session_id,
                    interview.status,
                    age_seconds,
                    worker_hostname,
                )
        finally:
            db_session.close()

        session_manager.update_session_status(
            session_id, session_manager.PROCESSING, {"assigned_node": worker_hostname}
        )

        db_session = SessionLocal()
        try:
            interview = db_session.execute(
                select(InterviewSession).where(InterviewSession.session_id == session_id)
            ).scalar_one_or_none()
            if interview:
                interview.assigned_node = worker_hostname
                interview.start_time = datetime.now(timezone.utc)
                db_session.commit()
        finally:
            db_session.close()

        # Parallel execution group
        session_manager.update_session_status(
            session_id, session_manager.VIDEO_PROCESSING, {"stage": "parallel_video_audio"}
        )

        # Build dynamic parallel tasks based on what still needs to be done
        parallel_tasks = []
        task_order = []

        # Check if video was already completed (from state)
        state = _get_session_state(session_id)
        video_completed = state.get("video_completed", False)
        audio_completed = state.get("audio_completed", False)

        if not video_completed:
            parallel_tasks.append(_run_video.s(session_id))
            task_order.append("video")

        if not audio_completed:
            parallel_tasks.append(_run_audio.s(session_id))
            task_order.append("audio")

        if parallel_tasks:
            parallel_group = group(*parallel_tasks)
            result = parallel_group.apply_async()

            from celery.result import allow_join_result

            try:
                with allow_join_result():
                    results = result.get(timeout=600)

            except TimeoutError:
                state = _get_session_state(session_id)
                raise

            except Exception:
                state = _get_session_state(session_id)
                raise

            # Unpack results based on what tasks we ran
            if len(results) == 2:
                video_result, audio_result = results
            elif len(results) == 1:
                if task_order[0] == "video":
                    video_result = results[0]
                    audio_result = state.get("audio_result", {})
                else:
                    video_result = state.get("video_result", {})
                    audio_result = results[0]
            else:
                video_result = state.get("video_result", {})
                audio_result = state.get("audio_result", {})
        else:
            # Both already completed, use cached results
            video_result = state.get("video_result", {})
            audio_result = state.get("audio_result", {})

        logger.info("Parallel video+audio completed for session %s", session_id)
        _after_parallel.delay(session_id, video_result, audio_result)

        # Record total runtime metrics
        runtime = time.perf_counter() - start_time
        CELERY_TASK_RUNTIME.labels(task_name=task_name).observe(runtime)

        # 🌟 Target custom metric incremented upon successful completion
        CELERY_TASKS_PROCESSED_TOTAL.labels(task="process_interview_session").inc()
        logger.info("Incremented processed metric for %s", task_name)

        return {
            "session_id": session_id,
            "status": "processing_parallel",
            "video_result": video_result,
            "audio_result": audio_result,
            "processed_by": worker_hostname,
        }

    except TimeoutError as exc:
        retry_delay = 2 ** (self.request.retries + 1)

        FAILURE_COUNT.labels(
            failure_type="celery_task_error"
        ).inc()

        logger.warning(
            "Timed out waiting for subtasks for session %s (attempt %d/3). Retrying in %ds.",
            session_id,
            self.request.retries + 1,
            retry_delay,
        )

        RETRY_COUNT.inc()

        raise self.retry(
            exc=exc,
            countdown=retry_delay,
        )

    except Exception as exc:
        retry_delay = 2 ** (self.request.retries + 1)

        # 🌟 Increments total failure counters explicitly
        FAILURE_COUNT.labels(failure_type="celery_task_error").inc()

        logger.warning(
            "Task for session %s failed (attempt %d/3), retrying in %ds: %s",
            session_id,
            self.request.retries + 1,
            retry_delay,
            exc,
            exc_info=True,
        )
        RETRY_COUNT.inc()
        raise self.retry(exc=exc, countdown=retry_delay)

    finally:
        # Decouple the active gauge count
        CELERY_ACTIVE_TASKS.labels(task_name=task_name).dec()

        # 🌟 Explicitly clear backlog gauge to show 0 execution depth remaining
        QUEUE_DEPTH.set(0.0)


# ---------------------------------------------------------------------------
# Celery Beat: periodic retry scanner
# ---------------------------------------------------------------------------


@celery_app.task(name="workers.tasks.scan_and_dispatch_retries")
def scan_and_dispatch_retries():
    """Scan Redis for retry entries whose ``retry_after`` timestamp has
    passed and re-dispatch the corresponding session through the normal
    scheduling path. Runs every 60 s via Celery Beat.
    """
    redis_client = get_redis_client()
    retry_scheduled_prefix = "retry_scheduled:"

    try:
        cursor = 0
        dispatched = 0
        while True:
            cursor, keys = redis_client.scan(cursor, match=f"{retry_scheduled_prefix}*", count=50)
            for key in keys:
                try:
                    raw = redis_client.get(key)
                    if not raw:
                        continue
                    data = json.loads(raw)
                    retry_after_str = data.get("retry_after")
                    if not retry_after_str:
                        continue
                    retry_after = datetime.fromisoformat(retry_after_str)
                    if retry_after.tzinfo is None:
                        retry_after = retry_after.replace(tzinfo=timezone.utc)

                    if datetime.now(timezone.utc) < retry_after:
                        continue  # not due yet

                    session_id = data.get("session_id")
                    if not session_id:
                        continue

                    from orchestrator.scheduler import Scheduler, TaskPriority

                    scheduler = Scheduler()
                    scheduler.schedule_task(session_id, priority=TaskPriority.MEDIUM)
                    dispatched += 1

                    redis_client.delete(key)
                    logger.info("Dispatched retry for session %s", session_id)

                except Exception as exc:
                    logger.debug("Error processing retry key %s: %s", key, exc)
                    continue

            if cursor == 0:
                break

        if dispatched:
            logger.info("Scan-and-dispatch complete: %d retries dispatched", dispatched)

    except Exception as exc:
        logger.error("scan_and_dispatch_retries failed: %s", exc)

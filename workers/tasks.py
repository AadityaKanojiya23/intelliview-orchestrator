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
from datetime import datetime, timezone

from celery import group
from sqlalchemy import select

from database.db import SessionLocal
from database.models import InterviewSession
from orchestrator.redis_client import get_redis_client
from orchestrator.session_manager import SessionManager
from orchestrator.state_sync import StateSynchronizer
from workers.celery_app import celery_app
from workers.evaluation_pipeline import evaluate_answers
from workers.risk_engine import RiskScoringEngine
from celery.exceptions import TimeoutError
from celery.result import AsyncResult

logger = logging.getLogger(__name__)

session_manager = SessionManager()
state_sync = StateSynchronizer()

def _get_session_state(session_id: str) -> dict:
    """Get cached session state from Redis."""
    state = session_manager.state_sync.get_session_state(session_id)
    return state or {}


def _update_session_state(session_id: str, **kwargs) -> None:
    """Merge additional fields into the cached session state."""
    state = _get_session_state(session_id)
    state.update(kwargs)
    session_manager.state_sync.set_session_state(session_id, state)

# ---------------------------------------------------------------------------
# Individual stage tasks
# ---------------------------------------------------------------------------


@celery_app.task(bind=True, max_retries=3, name="workers.tasks._run_video")
def _run_video(self, session_id: str) -> dict:
    """Video analysis stage."""
    from workers.video_pipeline import run_video_analysis

    result = run_video_analysis(session_id)

    _update_session_state(
        session_id,
        video_completed=True,
        video_result=result,
    )

    return result


@celery_app.task(bind=True, max_retries=3, name="workers.tasks._run_audio")
def _run_audio(self, session_id: str) -> dict:
    """Audio analysis stage."""
    from workers.audio_pipeline import run_audio_analysis

    result = run_audio_analysis(session_id)

    _update_session_state(
        session_id,
        audio_completed=True,
        audio_result=result,
    )

    return result


# ---------------------------------------------------------------------------
# Callback after parallel video + audio complete
# ---------------------------------------------------------------------------


@celery_app.task(name="workers.tasks._after_parallel")
def _after_parallel(session_id: str, video_result: dict, audio_result: dict):
    """Runs after video + audio group completes; then evaluation + risk."""
    try:
        logger.info("Parallel video+audio done for %s - running evaluation", session_id)

        session_manager.update_session_status(session_id, session_manager.EVALUATING, {"stage": "evaluation"})
        evaluation_result = evaluate_answers(session_id)
        logger.info("Answer evaluation completed for session %s", session_id)

        risk_report = RiskScoringEngine.generate_risk_report(
            session_id, video_result, audio_result, evaluation_result
        )
        final_risk_score = risk_report["final_risk_score"]
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
        session_manager.mark_session_failed(session_id, f"Post-parallel stage failed: {exc}")


# ---------------------------------------------------------------------------
# Main entry-point task
# ---------------------------------------------------------------------------


@celery_app.task(bind=True, max_retries=3, name="workers.tasks.process_interview_session")
def process_interview_session(self, session_id):
    """Run video + audio + evaluation + risk scoring for one session.

    Video and audio run in parallel via a Celery group; the evaluation
    and risk scoring stages run sequentially after both complete.
    """
    worker_hostname = socket.gethostname()
    
    try:
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
        # Load previously saved orchestration state
        session_state = _get_session_state(session_id)

        video_completed = session_state.get("video_completed", False)
        audio_completed = session_state.get("audio_completed", False)

        video_result = session_state.get("video_result")
        audio_result = session_state.get("audio_result")

       
        # Parallel: video + audio via Celery group
        session_manager.update_session_status(
            session_id, session_manager.VIDEO_PROCESSING, {"stage": "parallel_video_audio"}
        )
         

        # Build only the tasks that still need to run
        parallel_tasks = []
        task_order = []

        if not video_completed:
            parallel_tasks.append(_run_video.s(session_id))
            task_order.append("video")

        if not audio_completed:
            parallel_tasks.append(_run_audio.s(session_id))
            task_order.append("audio")

        # Run only unfinished tasks
        if parallel_tasks:
            result = group(*parallel_tasks).apply_async()
                       

            try:
                outputs = result.get(timeout=600)

            except TimeoutError:
                # Temporary problem while waiting
                raise

            except Exception:
                # Refresh state in case one task finished before the other failed
                session_state = _get_session_state(session_id)

                video_completed = session_state.get("video_completed", False)
                audio_completed = session_state.get("audio_completed", False)

                video_result = session_state.get("video_result")
                audio_result = session_state.get("audio_result")

                # Retry process_interview_session.
                # Completed subtasks will be skipped on the next run.
                raise

            if len(task_order) == 1:
                outputs = [outputs]

            for stage, output in zip(task_order, outputs):
                if stage == "video":
                    video_result = output
                    video_completed = True
                else:
                    audio_result = output
                    audio_completed = True

            logger.info(
                "Completed pending parallel tasks for session %s",
                session_id,
            )
        else:
            logger.info(
                "Video and audio already completed for session %s",
                session_id,
            )

        # Continue only when both results are available
        if video_completed and audio_completed:
            _after_parallel.delay(session_id, video_result, audio_result)

        return {
            "session_id": session_id,
            "status": "processing_parallel",
            "video_result": video_result,
            "audio_result": audio_result,
            "processed_by": worker_hostname,
        }
    except TimeoutError as exc:
        retry_delay = 2 ** (self.request.retries + 1)

        logger.warning(
            "Timed out waiting for subtasks for session %s (attempt %d/3). Retrying in %ds.",
            session_id,
            self.request.retries + 1,
            retry_delay,
        )

        raise self.retry(exc=exc, countdown=retry_delay)

    except Exception as exc:
        logger.error(
            "Processing failed for session %s: %s",
            session_id,
            exc,
            exc_info=True,
        )
        raise


# ---------------------------------------------------------------------------
# Celery Beat: periodic retry scanner
# ---------------------------------------------------------------------------


@celery_app.task(name="workers.tasks.scan_and_dispatch_retries")
def scan_and_dispatch_retries():
    """Scan Redis for retry entries whose ``retry_after`` timestamp has
    passed and re-dispatch the corresponding session through the normal
    scheduling path.  Runs every 60 s via Celery Beat.
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

                    # Dispatch via the normal scheduling path
                    from orchestrator.scheduler import Scheduler, TaskPriority

                    scheduler = Scheduler()
                    scheduler.schedule_task(session_id, priority=TaskPriority.MEDIUM)
                    dispatched += 1

                    # Clean up the scheduled key
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

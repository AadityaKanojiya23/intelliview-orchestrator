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

logger = logging.getLogger(__name__)

session_manager = SessionManager()
state_sync = StateSynchronizer()


# ---------------------------------------------------------------------------
# Individual stage tasks
# ---------------------------------------------------------------------------


@celery_app.task(bind=True, max_retries=3, name="workers.tasks._run_video")
def _run_video(self, session_id: str) -> dict:
    """Video analysis stage."""
    from workers.video_pipeline import run_video_analysis

    return run_video_analysis(session_id)


@celery_app.task(bind=True, max_retries=3, name="workers.tasks._run_audio")
def _run_audio(self, session_id: str) -> dict:
    """Audio analysis stage."""
    from workers.audio_pipeline import run_audio_analysis

    return run_audio_analysis(session_id)


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
    registry = WorkerRegistry()

    try:
        logger.info("Worker %s starting interview session: %s", worker_hostname, session_id)

        db_session = SessionLocal()
        try:
            interview = db_session.execute(
                select(InterviewSession).where(InterviewSession.session_id == session_id)
            ).scalar_one_or_none()

            if interview is None:
                logger.error("Session %s not found in DB", session_id)
                return {
                    "session_id": session_id,
                    "status": "missing",
                }

            if interview.status == "FAILED":
                interview.status = "QUEUED"
                db_session.commit()

        finally:
            db_session.close()

        session_manager.update_session_status(
            session_id,
            session_manager.PROCESSING,
            {"assigned_node": worker_hostname},
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

        # Parallel: video + audio via Celery group
        session_manager.update_session_status(
            session_id,
            session_manager.VIDEO_PROCESSING,
            {"stage": "parallel_video_audio"},
        )

        parallel_group = group(
            _run_video.s(session_id),
            _run_audio.s(session_id),
        )

        result = parallel_group.apply_async()

        # Wait for both to finish
        video_result, audio_result = result.get(timeout=600)

        logger.info(
            "Parallel video+audio completed for session %s",
            session_id,
        )

        # Continue with evaluation
        _after_parallel.delay(session_id, video_result, audio_result)

        # Record successful task completion
        registry.record_success(worker_hostname)

        return {
            "session_id": session_id,
            "status": "processing_parallel",
            "video_result": video_result,
            "audio_result": audio_result,
            "processed_by": worker_hostname,
        }

    except Exception as exc:

        # Record worker failure
        registry.record_failure(worker_hostname)

        retry_delay = 2 ** (self.request.retries + 1)

        logger.warning(
            "Task for session %s failed (attempt %d/3), retrying in %ds: %s",
            session_id,
            self.request.retries + 1,
            retry_delay,
            exc,
            exc_info=True,
        )

        raise self.retry(exc=exc, countdown=retry_delay)
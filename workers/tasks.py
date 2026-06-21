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

import logging
import socket
from datetime import datetime, timezone

from sqlalchemy import select

from database.db import SessionLocal
from database.models import InterviewSession
from orchestrator.session_manager import SessionManager
from orchestrator.state_sync import StateSynchronizer
from workers.audio_pipeline import run_audio_analysis
from workers.celery_app import celery_app
from workers.evaluation_pipeline import evaluate_answers
from workers.risk_engine import RiskScoringEngine
from workers.video_pipeline import run_video_analysis

logger = logging.getLogger(__name__)

session_manager = SessionManager()
state_sync = StateSynchronizer()


@celery_app.task(bind=True, max_retries=3, name="workers.tasks.process_interview_session")
def process_interview_session(self, session_id):
    """Run video + audio + evaluation + risk scoring for one session."""
    worker_hostname = socket.gethostname()

    try:
        logger.info("Worker %s starting interview session: %s", worker_hostname, session_id)

        # Idempotent reset for retries: if this is a retry attempt, the
        # session may be in FAILED state from a previous attempt that we
        # never want to surface to the user. Reset to QUEUED first so the
        # state machine accepts the transition to PROCESSING.
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

        # Stage 0: claim the session
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

        # Stage 1: video
        session_manager.update_session_status(
            session_id, session_manager.VIDEO_PROCESSING, {"stage": "video_analysis"}
        )
        video_result = run_video_analysis(session_id)
        logger.info("Video analysis completed for session %s", session_id)

        # Stage 2: audio
        session_manager.update_session_status(
            session_id, session_manager.AUDIO_PROCESSING, {"stage": "audio_analysis"}
        )
        audio_result = run_audio_analysis(session_id)
        logger.info("Audio analysis completed for session %s", session_id)

        # Stage 3: evaluation
        session_manager.update_session_status(session_id, session_manager.EVALUATING, {"stage": "evaluation"})
        evaluation_result = evaluate_answers(session_id)
        logger.info("Answer evaluation completed for session %s", session_id)

        # Stage 4: risk + completion (single atomic write)
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

        # Atomically mark complete (updates status + risk in one call)
        session_manager.mark_session_completed(session_id, final_risk_score)

        # Invalidate the stale Redis cache so the next read pulls fresh DB state.
        state_sync.delete_session_state(session_id)

        result = {
            "session_id": session_id,
            "status": "completed",
            "video_result": video_result,
            "audio_result": audio_result,
            "evaluation_result": evaluation_result,
            "risk_report": risk_report,
            "final_risk_score": final_risk_score,
            "risk_classification": risk_classification,
            "processed_by": worker_hostname,
            "timestamp": now.isoformat(),
        }
        logger.info("Successfully completed processing for session %s", session_id)
        return result

    except Exception as exc:
        # On transient failure: don't pollute the dashboard with FAILED.
        # Let Celery retry with exponential backoff. If retries are
        # exhausted, the task_failure signal (in celery_app.py) marks
        # the session FAILED so the operator sees the real terminal state.
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

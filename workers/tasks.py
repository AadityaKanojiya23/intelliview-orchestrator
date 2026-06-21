"""
Celery Tasks for Interview Processing
Defines tasks executed by worker nodes

Integrated with SessionManager for proper state lifecycle management.

Execution Flow:
1. QUEUED → PROCESSING (update status with worker node info)
2. PROCESSING → VIDEO_PROCESSING (update detailed status)
3. VIDEO_PROCESSING → AUDIO_PROCESSING (run audio pipeline)
4. AUDIO_PROCESSING → EVALUATING (run evaluation pipeline)
5. EVALUATING → COMPLETED (generate risk report, store results)
6. On Error: PROCESSING → FAILED (handle failures gracefully)
"""

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

# Initialize managers
session_manager = SessionManager()
state_sync = StateSynchronizer()


@celery_app.task(bind=True, max_retries=3)
def process_interview_session(self, session_id):
    """
    Main interview processing task executed by worker nodes

    This is the primary task that orchestrates all interview analysis pipelines
    with full lifecycle state management.

    Execution states:
    1. QUEUED → PROCESSING (worker assignment)
    2. PROCESSING → VIDEO_PROCESSING
    3. VIDEO_PROCESSING → AUDIO_PROCESSING
    4. AUDIO_PROCESSING → EVALUATING
    5. EVALUATING → COMPLETED (store results)

    Args:
        session_id: Unique identifier for the interview session

    Returns:
        dict: Results containing all analysis data and risk report

    Raises:
        Exception: On processing failure, task will retry with exponential backoff
    """
    worker_hostname = socket.gethostname()

    try:
        logger.info(f"Worker {worker_hostname} starting interview session: {session_id}")

        # Update status to PROCESSING
        logger.info(f"Updating session {session_id} to PROCESSING status")
        session_manager.update_session_status(
            session_id, session_manager.PROCESSING, {"assigned_node": worker_hostname}
        )

        # Update database with start time and assigned node
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

        # ========== STAGE 1: VIDEO ANALYSIS ==========

        logger.info(f"Stage 1/4: Video analysis for session {session_id}")
        session_manager.update_session_status(
            session_id, session_manager.VIDEO_PROCESSING, {"stage": "video_analysis"}
        )

        video_result = run_video_analysis(session_id)
        logger.info(f"Video analysis completed for session {session_id}")

        # ========== STAGE 2: AUDIO ANALYSIS ==========

        logger.info(f"Stage 2/4: Audio analysis for session {session_id}")
        session_manager.update_session_status(
            session_id, session_manager.AUDIO_PROCESSING, {"stage": "audio_analysis"}
        )

        audio_result = run_audio_analysis(session_id)
        logger.info(f"Audio analysis completed for session {session_id}")

        # ========== STAGE 3: ANSWER EVALUATION ==========

        logger.info(f"Stage 3/4: Answer evaluation for session {session_id}")
        session_manager.update_session_status(session_id, session_manager.EVALUATING, {"stage": "evaluation"})

        evaluation_result = evaluate_answers(session_id)
        logger.info(f"Answer evaluation completed for session {session_id}")

        # ========== STAGE 4: RISK CALCULATION & COMPLETION ==========

        logger.info(f"Stage 4/4: Risk calculation for session {session_id}")

        # Generate comprehensive risk report
        risk_report = RiskScoringEngine.generate_risk_report(
            session_id, video_result, audio_result, evaluation_result
        )

        final_risk_score = risk_report["final_risk_score"]
        risk_classification = risk_report["risk_classification"]
        logger.info(f"Risk report: {risk_classification} (score: {final_risk_score})")

        # Store results in database
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
                interview.end_time = datetime.now(timezone.utc)
                db_session.commit()
                logger.info(f"Stored results for session {session_id}")
        finally:
            db_session.close()

        # Mark session as completed via session manager
        session_manager.mark_session_completed(session_id, final_risk_score)
        logger.info(f"Session {session_id} marked COMPLETED with risk score {final_risk_score}")

        # Update cache
        session_data = state_sync.get_session_state(session_id)
        if session_data:
            session_data["status"] = session_manager.COMPLETED
            session_data["risk_score"] = final_risk_score
            session_data["risk_classification"] = risk_classification
            session_data["end_time"] = datetime.now(timezone.utc).isoformat()
            state_sync.set_session_state(session_id, session_data)

        # Prepare result
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
            "timestamp": datetime.now(timezone.utc).isoformat(),
        }

        logger.info(f"Successfully completed processing for session {session_id}")
        return result

    except Exception as exc:
        logger.error(f"Error processing session {session_id}: {exc!s}", exc_info=True)

        # Mark session as failed via session manager
        try:
            session_manager.mark_session_failed(session_id, f"Processing failed: {exc!s}")
            logger.info(f"Session {session_id} marked FAILED")
        except Exception as e:
            logger.error(f"Error marking session failed: {e!s}")

        # Retry with exponential backoff (2^retries seconds)
        retry_delay = 2**self.request.retries
        logger.info(f"Retrying task in {retry_delay}s (attempt {self.request.retries + 1}/3)")
        raise self.retry(exc=exc, countdown=retry_delay)


def sync_session_cache_to_db(session_id: str) -> bool:
    """
    Manually sync session cache to database

    Args:
        session_id: Interview session identifier

    Returns:
        bool: True if successful
    """
    try:
        session_data = state_sync.get_session_state(session_id)
        if session_data:
            return state_sync.sync_state_to_db(session_id, session_data)
        return False
    except Exception as e:
        logger.error(f"Error syncing session cache: {e!s}")
        return False

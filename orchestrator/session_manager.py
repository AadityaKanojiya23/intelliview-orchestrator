"""
Session Manager
Manages the complete lifecycle of interview sessions

Responsibilities:
- Create new interview sessions
- Update session state
- Retrieve session details
- Handle session transitions
- Maintain consistency between Redis and PostgreSQL
"""

import logging
from typing import Optional, Dict, Any
from datetime import datetime
from sqlalchemy import select
from database.db import SessionLocal
from database.models import InterviewSession
from orchestrator.state_sync import StateSynchronizer

logger = logging.getLogger(__name__)


class SessionManager:
    """
    Manages interview session lifecycle and state transitions
    """
    
    # Session states
    CREATED = "CREATED"
    QUEUED = "QUEUED"
    VIDEO_PROCESSING = "VIDEO_PROCESSING"
    AUDIO_PROCESSING = "AUDIO_PROCESSING"
    EVALUATING = "EVALUATING"
    PROCESSING = "PROCESSING"
    COMPLETED = "COMPLETED"
    FAILED = "FAILED"
    TIMEOUT = "TIMEOUT"
    CANCELLED = "CANCELLED"
    
    # Valid state transitions. The pipeline goes through a sequence of
    # granular PROCESSING sub-states before reaching COMPLETED.
    VALID_TRANSITIONS = {
        CREATED: [QUEUED, FAILED, CANCELLED],
        QUEUED: [PROCESSING, VIDEO_PROCESSING, FAILED, CANCELLED],
        PROCESSING: [VIDEO_PROCESSING, AUDIO_PROCESSING, EVALUATING, COMPLETED, FAILED, TIMEOUT],
        VIDEO_PROCESSING: [AUDIO_PROCESSING, PROCESSING, FAILED, TIMEOUT],
        AUDIO_PROCESSING: [EVALUATING, PROCESSING, FAILED, TIMEOUT],
        EVALUATING: [COMPLETED, PROCESSING, FAILED, TIMEOUT],
        COMPLETED: [],
        FAILED: [],
        TIMEOUT: [FAILED],
        CANCELLED: [],
    }
    
    # Timeout thresholds (in seconds)
    PROCESSING_TIMEOUT = 1800  # 30 minutes
    QUEUED_TIMEOUT = 3600      # 60 minutes
    
    def __init__(self):
        """Initialize session manager with state synchronizer"""
        self.state_sync = StateSynchronizer()
    
    def create_session(self, candidate_id: str, position: Optional[str] = None,
                      candidate_name: Optional[str] = None) -> str:
        """
        Create a new interview session
        
        Args:
            candidate_id: Unique candidate identifier
            position: Job position for the interview
            candidate_name: Candidate's name
            
        Returns:
            str: Generated session_id
        """
        session_db = SessionLocal()
        try:
            # Generate unique session ID
            session_id = f"session_{datetime.utcnow().strftime('%Y%m%d%H%M%S')}_{hash(candidate_id) % 100000:05d}"
            
            logger.info(f"Creating new interview session: {session_id} for candidate {candidate_id}")
            
            # Create database record
            interview_session = InterviewSession(
                session_id=session_id,
                candidate_id=candidate_id,
                status=self.CREATED,
                created_at=datetime.utcnow(),
                updated_at=datetime.utcnow()
            )
            
            session_db.add(interview_session)
            session_db.commit()
            
            # Sync to Redis cache
            session_data = {
                "session_id": session_id,
                "candidate_id": candidate_id,
                "candidate_name": candidate_name or "Unknown",
                "position": position or "Unknown",
                "status": self.CREATED,
                "created_at": datetime.utcnow().isoformat(),
                "updated_at": datetime.utcnow().isoformat(),
                "risk_score": None
            }
            self.state_sync.set_session_state(session_id, session_data)
            
            logger.info(f"Session {session_id} created successfully")
            return session_id
            
        except Exception as e:
            logger.error(f"Error creating session: {str(e)}")
            session_db.rollback()
            raise
        finally:
            session_db.close()
    
    def update_session_status(self, session_id: str, new_status: str,
                             metadata: Optional[Dict[str, Any]] = None) -> bool:
        """
        Update session status with validation
        
        Args:
            session_id: Session identifier
            new_status: New status to set
            metadata: Optional additional data to store
            
        Returns:
            bool: True if successful, False otherwise
        """
        session_db = SessionLocal()
        try:
            # Get current session
            interview = session_db.execute(
                select(InterviewSession).where(InterviewSession.session_id == session_id)
            ).scalar_one_or_none()
            
            if not interview:
                logger.error(f"Session {session_id} not found")
                return False
            
            current_status = interview.status
            
            # Validate state transition
            if not self._is_valid_transition(current_status, new_status):
                logger.warning(
                    f"Invalid state transition: {current_status} -> {new_status} for session {session_id}"
                )
                return False
            
            logger.info(f"Updating session {session_id} status: {current_status} -> {new_status}")
            
            # Update database
            interview.status = new_status
            interview.updated_at = datetime.utcnow()
            session_db.commit()
            
            # Update Redis cache
            session_data = self.state_sync.get_session_state(session_id)
            if session_data:
                session_data["status"] = new_status
                session_data["updated_at"] = datetime.utcnow().isoformat()
                if metadata:
                    session_data.update(metadata)
                self.state_sync.set_session_state(session_id, session_data)
            
            logger.info(f"Session {session_id} status updated to {new_status}")
            return True
            
        except Exception as e:
            logger.error(f"Error updating session status: {str(e)}")
            session_db.rollback()
            return False
        finally:
            session_db.close()
    
    def get_session(self, session_id: str) -> Optional[Dict[str, Any]]:
        """
        Retrieve session details
        
        Args:
            session_id: Session identifier
            
        Returns:
            dict: Session details or None if not found
        """
        try:
            # Try to get from Redis cache first (fast path)
            session_data = self.state_sync.get_session_state(session_id)
            if session_data:
                logger.debug(f"Retrieved session {session_id} from cache")
                return session_data
            
            # Fall back to database
            session_db = SessionLocal()
            try:
                interview = session_db.execute(
                    select(InterviewSession).where(InterviewSession.session_id == session_id)
                ).scalar_one_or_none()
                
                if not interview:
                    logger.warning(f"Session {session_id} not found")
                    return None
                
                # Convert to dict for consistency
                session_data = {
                    "session_id": interview.session_id,
                    "candidate_id": interview.candidate_id,
                    "status": interview.status,
                    "risk_score": interview.risk_score,
                    "assigned_node": interview.assigned_node,
                    "start_time": interview.start_time.isoformat() if interview.start_time else None,
                    "end_time": interview.end_time.isoformat() if interview.end_time else None,
                    "created_at": interview.created_at.isoformat() if interview.created_at else None,
                    "updated_at": interview.updated_at.isoformat() if interview.updated_at else None,
                    "video_analysis": interview.video_analysis,
                    "audio_analysis": interview.audio_analysis,
                    "evaluation_analysis": interview.evaluation_analysis
                }
                
                # Update Redis cache for next lookup
                self.state_sync.set_session_state(session_id, session_data)
                
                logger.debug(f"Retrieved session {session_id} from database")
                return session_data
                
            finally:
                session_db.close()
                
        except Exception as e:
            logger.error(f"Error retrieving session: {str(e)}")
            return None
    
    def mark_session_failed(self, session_id: str, error_message: str) -> bool:
        """
        Mark a session as failed with error details
        
        Args:
            session_id: Session identifier
            error_message: Error message describing the failure
            
        Returns:
            bool: True if successful
        """
        logger.warning(f"Marking session {session_id} as failed: {error_message}")
        
        return self.update_session_status(
            session_id,
            self.FAILED,
            {"error_message": error_message}
        )
    
    def mark_session_completed(self, session_id: str, risk_score: float) -> bool:
        """
        Mark a session as completed with final risk score
        
        Args:
            session_id: Session identifier
            risk_score: Final calculated risk score
            
        Returns:
            bool: True if successful
        """
        logger.info(f"Marking session {session_id} as completed with risk score {risk_score}")
        
        session_db = SessionLocal()
        try:
            interview = session_db.execute(
                select(InterviewSession).where(InterviewSession.session_id == session_id)
            ).scalar_one_or_none()
            
            if not interview:
                return False
            
            interview.status = self.COMPLETED
            interview.risk_score = risk_score
            interview.end_time = datetime.utcnow()
            interview.updated_at = datetime.utcnow()
            session_db.commit()
            
            # Update Redis
            session_data = self.state_sync.get_session_state(session_id)
            if session_data:
                session_data["status"] = self.COMPLETED
                session_data["risk_score"] = risk_score
                session_data["end_time"] = datetime.utcnow().isoformat()
                session_data["updated_at"] = datetime.utcnow().isoformat()
                self.state_sync.set_session_state(session_id, session_data)
            
            logger.info(f"Session {session_id} marked as completed")
            return True
            
        except Exception as e:
            logger.error(f"Error marking session completed: {str(e)}")
            session_db.rollback()
            return False
        finally:
            session_db.close()
    
    def cancel_session(self, session_id: str, reason: str) -> bool:
        """
        Cancel an ongoing session
        
        Args:
            session_id: Session identifier
            reason: Reason for cancellation
            
        Returns:
            bool: True if successful
        """
        logger.info(f"Cancelling session {session_id}: {reason}")
        return self.update_session_status(
            session_id,
            self.CANCELLED,
            {"cancellation_reason": reason}
        )
    
    def _is_valid_transition(self, current_status: str, new_status: str) -> bool:
        """
        Check if state transition is valid
        
        Args:
            current_status: Current session status
            new_status: New status to transition to
            
        Returns:
            bool: True if transition is valid
        """
        if current_status not in self.VALID_TRANSITIONS:
            return False
        
        return new_status in self.VALID_TRANSITIONS[current_status]
    
    def detect_timeout_sessions(self) -> list:
        """
        Detect sessions that have timed out and mark as failed
        
        Returns:
            list: List of session_ids that timed out
        """
        session_db = SessionLocal()
        timed_out_sessions = []
        
        try:
            now = datetime.utcnow()
            
            # Check for PROCESSING sessions that have exceeded timeout
            processing_sessions = session_db.execute(
                select(InterviewSession).where(InterviewSession.status == self.PROCESSING)
            ).scalars().all()
            
            for session in processing_sessions:
                elapsed_time = (now - session.start_time).total_seconds()
                if elapsed_time > self.PROCESSING_TIMEOUT:
                    logger.warning(
                        f"Session {session.session_id} timed out after {elapsed_time}s"
                    )
                    self.mark_session_failed(session.session_id, f"Processing timeout after {elapsed_time}s")
                    timed_out_sessions.append(session.session_id)
            
            # Check for QUEUED sessions that have exceeded timeout
            queued_sessions = session_db.execute(
                select(InterviewSession).where(InterviewSession.status == self.QUEUED)
            ).scalars().all()
            
            for session in queued_sessions:
                elapsed_time = (now - session.created_at).total_seconds()
                if elapsed_time > self.QUEUED_TIMEOUT:
                    logger.warning(
                        f"Session {session.session_id} stuck in QUEUED for {elapsed_time}s"
                    )
                    self.mark_session_failed(session.session_id, f"Queued timeout after {elapsed_time}s")
                    timed_out_sessions.append(session.session_id)
            
            return timed_out_sessions
            
        except Exception as e:
            logger.error(f"Error detecting timeout sessions: {str(e)}")
            return []
        finally:
            session_db.close()

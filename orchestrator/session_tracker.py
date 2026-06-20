"""
Session Tracker
Monitors and tracks interview session progress and status

Responsibilities:
- Track running sessions
- Detect stuck or inactive sessions
- Provide session statistics
- Monitor session health
"""

import logging
from typing import Dict, List, Any, Optional
from datetime import datetime, timedelta
from sqlalchemy import select, func
from database.db import SessionLocal
from database.models import InterviewSession

logger = logging.getLogger(__name__)


class SessionTracker:
    """
    Tracks and monitors interview sessions across the system
    """
    
    def __init__(self):
        """Initialize session tracker"""
        pass
    
    def get_active_sessions(self) -> List[Dict[str, Any]]:
        """
        Get all currently active sessions (CREATED, QUEUED, PROCESSING)
        
        Returns:
            list: List of active session details
        """
        session_db = SessionLocal()
        try:
            active_statuses = ["CREATED", "QUEUED", "PROCESSING", "VIDEO_PROCESSING", 
                              "AUDIO_PROCESSING", "EVALUATING"]
            sessions = session_db.execute(
                select(InterviewSession).where(InterviewSession.status.in_(active_statuses))
            ).scalars().all()
            
            result = []
            for s in sessions:
                result.append({
                    "session_id": s.session_id,
                    "candidate_id": s.candidate_id,
                    "status": s.status,
                    "assigned_node": s.assigned_node,
                    "created_at": s.created_at.isoformat() if s.created_at else None,
                    "updated_at": s.updated_at.isoformat() if s.updated_at else None
                })
            
            logger.debug(f"Retrieved {len(result)} active sessions")
            return result
            
        except Exception as e:
            logger.error(f"Error getting active sessions: {str(e)}")
            return []
        finally:
            session_db.close()
    
    def get_completed_sessions(self, limit: int = 100) -> List[Dict[str, Any]]:
        """
        Get recently completed sessions
        
        Args:
            limit: Maximum number of sessions to retrieve
            
        Returns:
            list: List of completed session details
        """
        session_db = SessionLocal()
        try:
            sessions = session_db.execute(
                select(InterviewSession).where(InterviewSession.status == "COMPLETED")
            ).scalars().all()
            
            durations = []
            for s in completed_sessions:
                duration = (s.end_time - s.start_time).total_seconds()
                durations.append(duration)
            
            avg_duration = sum(durations) / len(durations) if durations else 0
            
            # Calculate risk score statistics
            risk_scores = session_db.execute(
                select(InterviewSession.risk_score).where(InterviewSession.risk_score.isnot(None))
            ).scalars().all()
            
            risk_scores_list = [r[0] for r in risk_scores]
            avg_risk = sum(risk_scores_list) / len(risk_scores_list) if risk_scores_list else 0
            max_risk = max(risk_scores_list) if risk_scores_list else 0
            min_risk = min(risk_scores_list) if risk_scores_list else 0
            
            # Count high-risk sessions
            high_risk_count = session_db.execute(
                select(func.count()).select_from(InterviewSession).where(InterviewSession.risk_score >= 0.8)
            ).scalar() or 0
            
            stats = {
                "total_sessions": total_sessions,
                "status_breakdown": status_counts,
                "active_sessions": status_counts.get("PROCESSING", 0) + 
                                 status_counts.get("QUEUED", 0) +
                                 status_counts.get("VIDEO_PROCESSING", 0) +
                                 status_counts.get("AUDIO_PROCESSING", 0) +
                                 status_counts.get("EVALUATING", 0),
                "completed_sessions": status_counts.get("COMPLETED", 0),
                "failed_sessions": status_counts.get("FAILED", 0),
                "processing_stats": {
                    "average_duration_seconds": round(avg_duration, 2),
                    "completed_session_count": len(completed_sessions)
                },
                "risk_score_stats": {
                    "average_risk_score": round(avg_risk, 3),
                    "max_risk_score": round(max_risk, 3),
                    "min_risk_score": round(min_risk, 3),
                    "high_risk_sessions": high_risk_count
                }
            }
            
            logger.debug("Generated session statistics")
            return stats
            
        except Exception as e:
            logger.error(f"Error generating statistics: {str(e)}")
            return {}
        finally:
            session_db.close()
    
    def get_stuck_sessions(self, timeout_minutes: int = 30) -> List[Dict[str, Any]]:
        """
        Detect sessions that are stuck (in PROCESSING state beyond timeout)
        
        Args:
            timeout_minutes: Timeout threshold in minutes
            
        Returns:
            list: List of stuck session details
        """
        session_db = SessionLocal()
        try:
            cutoff_time = datetime.utcnow() - timedelta(minutes=timeout_minutes)
            
            stuck_sessions = session_db.execute(
                select(InterviewSession).where(
                    InterviewSession.status == "PROCESSING",
                    InterviewSession.start_time < cutoff_time,
                )
            ).scalars().all()
            
            result = []
            for s in stuck_sessions:
                elapsed_time = (datetime.utcnow() - s.start_time).total_seconds()
                result.append({
                    "session_id": s.session_id,
                    "candidate_id": s.candidate_id,
                    "status": s.status,
                    "assigned_node": s.assigned_node,
                    "start_time": s.start_time.isoformat() if s.start_time else None,
                    "elapsed_seconds": round(elapsed_time, 2)
                })
            
            if result:
                logger.warning(f"Found {len(result)} stuck sessions (timeout > {timeout_minutes} minutes)")
            
            return result
            
        except Exception as e:
            logger.error(f"Error detecting stuck sessions: {str(e)}")
            return []
        finally:
            session_db.close()
    
    def get_worker_distribution(self) -> Dict[str, int]:
        """
        Get distribution of active sessions across worker nodes
        
        Returns:
            dict: Worker node -> active session count mapping
        """
        session_db = SessionLocal()
        try:
            active_statuses = ["PROCESSING", "VIDEO_PROCESSING", "AUDIO_PROCESSING", "EVALUATING"]
            sessions = session_db.execute(
                select(InterviewSession).where(InterviewSession.status.in_(active_statuses))
            ).scalars().all()
            
            distribution = {}
            for s in sessions:
                node = s.assigned_node or "unassigned"
                distribution[node] = distribution.get(node, 0) + 1
            
            logger.debug(f"Worker distribution: {distribution}")
            return distribution
            
        except Exception as e:
            logger.error(f"Error getting worker distribution: {str(e)}")
            return {}
        finally:
            session_db.close()
    
    def get_high_risk_sessions(self, threshold: float = 0.8, limit: int = 50) -> List[Dict[str, Any]]:
        """
        Get high-risk sessions that completed
        
        Args:
            threshold: Risk score threshold (0-1)
            limit: Maximum number of sessions to retrieve
            
        Returns:
            list: List of high-risk sessions
        """
        session_db = SessionLocal()
        try:
            sessions = session_db.execute(
                select(InterviewSession)
                .where(
                    InterviewSession.risk_score >= threshold,
                    InterviewSession.status == "COMPLETED",
                )
                .order_by(InterviewSession.risk_score.desc())
                .limit(limit)
            ).scalars().all()
            
            result = []
            for s in sessions:
                result.append({
                    "session_id": s.session_id,
                    "candidate_id": s.candidate_id,
                    "risk_score": s.risk_score,
                    "status": s.status,
                    "completed_at": s.end_time.isoformat() if s.end_time else None
                })
            
            logger.debug(f"Retrieved {len(result)} high-risk sessions (threshold: {threshold})")
            return result
            
        except Exception as e:
            logger.error(f"Error getting high-risk sessions: {str(e)}")
            return []
        finally:
            session_db.close()
    
    @staticmethod
    def _calculate_duration(start_time, end_time) -> Optional[float]:
        """
        Calculate duration between two timestamps
        
        Args:
            start_time: Start timestamp
            end_time: End timestamp
            
        Returns:
            float: Duration in seconds or None
        """
        if not start_time or not end_time:
            return None
        
        try:
            duration = (end_time - start_time).total_seconds()
            return round(duration, 2)
        except Exception:
            return None

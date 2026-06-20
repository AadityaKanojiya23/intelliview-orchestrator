"""
SQLAlchemy ORM Models for AI Interview Orchestrator
Defines database models using declarative base
"""

from sqlalchemy import Column, String, Float, DateTime, JSON
from sqlalchemy.sql import func  # noqa: F401  (re-exported for ORM consumers)
from database.db import Base
from datetime import datetime


class InterviewSession(Base):
    """
    InterviewSession ORM Model
    Represents an interview session with candidate and processing details
    """
    __tablename__ = "interview_sessions"

    session_id = Column(String(255), primary_key=True, index=True, nullable=False)
    candidate_id = Column(String(255), nullable=False, index=True)
    status = Column(String(50), nullable=False, default="pending")
    assigned_node = Column(String(255), nullable=True)
    start_time = Column(DateTime, nullable=True, default=datetime.utcnow)
    end_time = Column(DateTime, nullable=True)
    risk_score = Column(Float, nullable=True)
    
    # Analysis results stored as JSON
    video_analysis = Column(JSON, nullable=True)
    audio_analysis = Column(JSON, nullable=True)
    evaluation_analysis = Column(JSON, nullable=True)
    
    created_at = Column(DateTime, nullable=False, default=datetime.utcnow)
    updated_at = Column(DateTime, nullable=False, default=datetime.utcnow, onupdate=datetime.utcnow)

    def __repr__(self):
        return f"<InterviewSession(session_id='{self.session_id}', candidate_id='{self.candidate_id}', status='{self.status}', risk_score={self.risk_score})>"

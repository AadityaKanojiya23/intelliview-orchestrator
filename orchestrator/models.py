from datetime import datetime
from sqlalchemy import Column, String, DateTime, Boolean, Integer
from sqlalchemy.ext.declarative import declarative_base

Base = declarative_base()

class RiskPredictionMonitoring(Base):
    __tablename__ = 'risk_prediction_monitoring'

    id = Column(Integer, primary_key=True, autoincrement=True)
    session_id = Column(String(255), nullable=False, index=True)
    predicted_risk_level = Column(String(50), nullable=False)  # Tracks 'HIGH'
    recruiter_outcome = Column(String(50), nullable=True)     # 'CONFIRM' or 'OVERRIDE'
    is_false_positive = Column(Boolean, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)

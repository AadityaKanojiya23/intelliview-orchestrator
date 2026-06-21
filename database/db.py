"""
Database connection manager for AI Interview Orchestrator
Centralizes SQLAlchemy connection and session management
"""

from sqlalchemy import create_engine
from sqlalchemy.orm import declarative_base, sessionmaker
from config import DATABASE_URL
import logging

logger = logging.getLogger(__name__)

# Create SQLAlchemy engine with connection-recycling and pre-ping so that
# stale connections (e.g., after a Postgres restart) are dropped instead of
# surfacing as "connection reset" errors to callers.
engine = create_engine(
    DATABASE_URL,
    echo=False,  # Set to True for SQL debugging
    pool_size=10,
    max_overflow=20,
    pool_pre_ping=True,
    pool_recycle=1800,
)

# Session factory
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Base model for ORM models
Base = declarative_base()


def get_db():
    """
    Dependency function for FastAPI to get database session
    """
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def init_db():
    """
    Initialize database tables
    Creates all tables defined in models
    """
    Base.metadata.create_all(bind=engine)
    logger.info("Database tables initialized")

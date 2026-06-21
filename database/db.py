"""Database connection manager for AI Interview Orchestrator.

Centralises SQLAlchemy connection and session management. Use `SessionLocal()`
as a context-manager (or close it manually) and prefer the type-hinted
`with SessionLocal() as db:` pattern in new code.
"""

from __future__ import annotations

import logging

from sqlalchemy import create_engine
from sqlalchemy.orm import declarative_base, sessionmaker

from config import DATABASE_URL

logger = logging.getLogger(__name__)

# Connection-recycling + pre-ping so stale Postgres connections (e.g., after
# a Postgres restart) are dropped instead of surfacing as
# "connection reset" errors to callers.
engine = create_engine(
    DATABASE_URL,
    echo=False,
    pool_size=10,
    max_overflow=20,
    pool_pre_ping=True,
    pool_recycle=1800,
)

# Session factory. Use as `with SessionLocal() as db: ...` for automatic
# cleanup, or call `db.close()` manually.
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Base class for ORM models.
Base = declarative_base()

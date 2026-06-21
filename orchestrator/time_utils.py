"""Timezone-aware datetime helpers used across the orchestrator.

Replaces the deprecated `datetime.utcnow()` with `datetime.now(timezone.utc)`
in one place so the rest of the codebase imports a stable name.
"""

from __future__ import annotations

from datetime import datetime, timezone


def utcnow() -> datetime:
    """Return the current UTC time as a timezone-aware datetime."""
    return datetime.now(timezone.utc)


__all__ = ["utcnow"]

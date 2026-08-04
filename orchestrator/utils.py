"""
Shared Utility Helpers — AI Interview Orchestrator
====================================================
Central location for small, reusable helper functions used across the
orchestrator package.

Functions
---------
utc_now_iso()       — current UTC timestamp as ISO-8601 string
is_coroutine()      — check if a callable is async
redis_json_get()    — safely fetch and JSON-decode a Redis key
redis_json_set()    — safely JSON-encode and store a value in Redis
log_event()         — emit a structured log event with arbitrary fields
"""

from __future__ import annotations

import inspect
import json
import logging
from collections.abc import Callable
from datetime import datetime, timezone
from typing import Any


def utc_now_iso() -> str:
    """Return the current UTC time as an ISO-8601 string."""
    return datetime.now(timezone.utc).isoformat()


def is_coroutine(fn: Callable) -> bool:
    """Return True if fn is an async (coroutine) function."""
    return inspect.iscoroutinefunction(fn)


def redis_json_get(client: Any, key: str) -> Any | None:
    """Fetch key from Redis and JSON-decode the result."""
    if client is None:
        return None
    try:
        raw = client.get(key)
        return json.loads(raw) if raw else None
    except Exception:
        return None


def redis_json_set(client: Any, key: str, value: Any, ttl: int | None = None) -> bool:
    """JSON-encode value and store it in Redis under key."""
    if client is None:
        return False
    try:
        payload = json.dumps(value, default=str)
        if ttl is not None:
            client.set(key, payload, ex=ttl)
        else:
            client.set(key, payload)
        return True
    except Exception:
        return False


def log_event(logger: logging.Logger, level: int, event: str, **fields: Any) -> None:
    """Emit a structured log event with arbitrary keyword fields."""
    logger.log(level, event, extra=fields)

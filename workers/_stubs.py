"""Shared stub helpers used by the AI analysis pipelines."""

import hashlib


def _seeded_unit(session_id: str, salt: str) -> float:
    """Stable pseudo-random in [0, 1) derived from session_id + salt."""
    digest = hashlib.sha256(f"{session_id}:{salt}".encode()).digest()
    return int.from_bytes(digest[:4], "big") / 0xFFFFFFFF

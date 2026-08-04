"""
store.py — In-memory config store
Simulates a database. Replace with SQLAlchemy/MongoDB adapter as needed.
"""

import uuid
from datetime import datetime, timezone

from models import RiskConfigCreate, RiskConfigResponse, RiskConfigUpdate, RiskWeights

# Default fallback config — used when no job-specific config exists
DEFAULT_WEIGHTS = RiskWeights()

_store: dict[str, dict] = {}


def _now():
    return datetime.now(timezone.utc)


def _to_response(record: dict) -> RiskConfigResponse:
    return RiskConfigResponse(**record)


# ── CRUD ──────────────────────────────────────────────────────────────────────


def create_config(data: RiskConfigCreate) -> RiskConfigResponse:
    # Prevent duplicate job positions
    for record in _store.values():
        if record["job_position"].lower() == data.job_position.lower():
            raise ValueError(
                f"Config for '{data.job_position}' already exists. Use PUT to update."
            )

    config_id = str(uuid.uuid4())
    now = _now()
    record = {
        "id": config_id,
        "job_position": data.job_position,
        "weights": data.weights,
        "description": data.description,
        "created_at": now,
        "updated_at": now,
    }
    _store[config_id] = record
    return _to_response(record)


def get_config(config_id: str) -> RiskConfigResponse | None:
    record = _store.get(config_id)
    return _to_response(record) if record else None


def get_config_by_position(job_position: str) -> RiskConfigResponse | None:
    for record in _store.values():
        if record["job_position"].lower() == job_position.lower():
            return _to_response(record)
    return None


def list_configs() -> list[RiskConfigResponse]:
    return [_to_response(r) for r in _store.values()]


def update_config(
    config_id: str, data: RiskConfigUpdate
) -> RiskConfigResponse | None:
    record = _store.get(config_id)
    if not record:
        return None
    if data.weights is not None:
        record["weights"] = data.weights
    if data.description is not None:
        record["description"] = data.description
    record["updated_at"] = _now()
    return _to_response(record)


def delete_config(config_id: str) -> bool:
    if config_id not in _store:
        return False
    del _store[config_id]
    return True


def get_weights_for_position(job_position: str) -> RiskWeights:
    """
    Used by the risk engine: returns job-specific weights if configured,
    else falls back to default weights. Existing functionality unaffected.
    """
    config = get_config_by_position(job_position)
    return config.weights if config else DEFAULT_WEIGHTS


def clear_all():
    """Test helper — resets store between tests."""
    _store.clear()

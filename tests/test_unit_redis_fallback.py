"""Unit tests for the Redis read-fallback to PostgreSQL (Feature #13).

Verifies that when the Redis circuit breaker is OPEN:
- get_session_state() reads from PostgreSQL
- get_active_sessions() reads from PostgreSQL
- session_manager skips Redis cache writes
"""

from unittest.mock import MagicMock, patch

import pytest

from orchestrator.redis_client import _CircuitState, circuit_breaker


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


@pytest.fixture(autouse=True)
def _reset_circuit_breaker():
    """Ensure the circuit breaker is CLOSED before and after each test."""
    circuit_breaker.reset()
    yield
    circuit_breaker.reset()


def _force_circuit_open():
    """Force the module-level circuit breaker into OPEN state."""
    circuit_breaker._state = _CircuitState.OPEN
    circuit_breaker._failure_count = circuit_breaker.failure_threshold


def _make_fake_session_row(session_id="sess_abc123", status="PROCESSING"):
    """Return a mock that looks like an InterviewSession ORM object."""
    row = MagicMock()
    row.session_id = session_id
    row.candidate_id = "cand_001"
    row.status = status
    row.risk_score = 0.42
    row.assigned_node = "worker-1"
    row.start_time = None
    row.end_time = None
    row.created_at = None
    row.updated_at = None
    row.video_analysis = None
    row.audio_analysis = None
    row.evaluation_analysis = None
    return row


# ---------------------------------------------------------------------------
# is_circuit_open()
# ---------------------------------------------------------------------------


def test_is_circuit_open_returns_false_when_closed():
    from orchestrator.redis_client import is_circuit_open

    assert is_circuit_open() is False


def test_is_circuit_open_returns_true_when_open():
    from orchestrator.redis_client import is_circuit_open

    _force_circuit_open()
    assert is_circuit_open() is True


# ---------------------------------------------------------------------------
# StateSynchronizer.get_session_state() fallback
# ---------------------------------------------------------------------------


@patch("orchestrator.state_sync.SessionLocal")
def test_get_session_state_falls_back_to_pg_when_circuit_open(mock_session_local):
    """When circuit is OPEN, get_session_state should query PG directly."""
    _force_circuit_open()

    fake_row = _make_fake_session_row("sess_xyz")
    mock_db = MagicMock()
    mock_db.execute.return_value.scalar_one_or_none.return_value = fake_row
    mock_session_local.return_value = mock_db

    from orchestrator.state_sync import StateSynchronizer

    sync = StateSynchronizer.__new__(StateSynchronizer)
    sync.redis_client = MagicMock()  # should not be called

    result = sync.get_session_state("sess_xyz")

    assert result is not None
    assert result["session_id"] == "sess_xyz"
    assert result["candidate_id"] == "cand_001"
    assert result["status"] == "PROCESSING"
    assert result["risk_score"] == 0.42
    # Redis should NOT have been called
    sync.redis_client.get.assert_not_called()
    mock_db.close.assert_called_once()


@patch("orchestrator.state_sync.SessionLocal")
def test_get_session_state_falls_back_on_redis_exception(mock_session_local):
    """When Redis raises, get_session_state should fall back to PG."""
    import redis as _redis

    fake_row = _make_fake_session_row("sess_err")
    mock_db = MagicMock()
    mock_db.execute.return_value.scalar_one_or_none.return_value = fake_row
    mock_session_local.return_value = mock_db

    from orchestrator.state_sync import StateSynchronizer

    sync = StateSynchronizer.__new__(StateSynchronizer)
    sync.redis_client = MagicMock()
    sync.redis_client.get.side_effect = _redis.ConnectionError("connection refused")

    result = sync.get_session_state("sess_err")

    assert result is not None
    assert result["session_id"] == "sess_err"
    mock_db.close.assert_called_once()


@patch("orchestrator.state_sync.SessionLocal")
def test_get_session_state_returns_none_when_not_in_pg(mock_session_local):
    """When circuit is OPEN and session doesn't exist in PG, return None."""
    _force_circuit_open()

    mock_db = MagicMock()
    mock_db.execute.return_value.scalar_one_or_none.return_value = None
    mock_session_local.return_value = mock_db

    from orchestrator.state_sync import StateSynchronizer

    sync = StateSynchronizer.__new__(StateSynchronizer)
    sync.redis_client = MagicMock()

    result = sync.get_session_state("nonexistent")

    assert result is None
    mock_db.close.assert_called_once()


# ---------------------------------------------------------------------------
# StateSynchronizer.get_active_sessions() fallback
# ---------------------------------------------------------------------------


@patch("orchestrator.state_sync.SessionLocal")
def test_get_active_sessions_falls_back_to_pg_when_circuit_open(mock_session_local):
    """When circuit is OPEN, get_active_sessions should query PG."""
    _force_circuit_open()

    mock_db = MagicMock()
    mock_db.execute.return_value.scalars.return_value.all.return_value = [
        "sess_1",
        "sess_2",
        "sess_3",
    ]
    mock_session_local.return_value = mock_db

    from orchestrator.state_sync import StateSynchronizer

    sync = StateSynchronizer.__new__(StateSynchronizer)
    sync.redis_client = MagicMock()

    result = sync.get_active_sessions()

    assert result == ["sess_1", "sess_2", "sess_3"]
    sync.redis_client.smembers.assert_not_called()
    mock_db.close.assert_called_once()


@patch("orchestrator.state_sync.SessionLocal")
def test_get_active_sessions_falls_back_on_redis_exception(mock_session_local):
    """When Redis raises, get_active_sessions should fall back to PG."""
    import redis as _redis

    mock_db = MagicMock()
    mock_db.execute.return_value.scalars.return_value.all.return_value = ["sess_a"]
    mock_session_local.return_value = mock_db

    from orchestrator.state_sync import StateSynchronizer

    sync = StateSynchronizer.__new__(StateSynchronizer)
    sync.redis_client = MagicMock()
    sync.redis_client.smembers.side_effect = _redis.ConnectionError("timeout")

    result = sync.get_active_sessions()

    assert result == ["sess_a"]
    mock_db.close.assert_called_once()


# ---------------------------------------------------------------------------
# SessionManager skips Redis writes when circuit is open
# ---------------------------------------------------------------------------


@patch("orchestrator.session_manager.SessionLocal")
def test_update_session_status_skips_cache_write_when_circuit_open(mock_session_local):
    """When circuit is OPEN, update_session_status should NOT write to Redis."""
    _force_circuit_open()

    # Mock the DB session and row
    fake_row = _make_fake_session_row("sess_skip", status="QUEUED")
    mock_db = MagicMock()
    mock_db.execute.return_value.scalar_one_or_none.return_value = fake_row
    mock_session_local.return_value = mock_db

    from orchestrator.session_manager import SessionManager

    sm = SessionManager.__new__(SessionManager)
    sm.state_sync = MagicMock()

    result = sm.update_session_status("sess_skip", "PROCESSING")

    assert result is True
    # state_sync.get_session_state should NOT be called for cache update
    sm.state_sync.get_session_state.assert_not_called()
    sm.state_sync.set_session_state.assert_not_called()


@patch("orchestrator.session_manager.SessionLocal")
def test_mark_session_completed_skips_cache_write_when_circuit_open(mock_session_local):
    """When circuit is OPEN, mark_session_completed should NOT write to Redis."""
    _force_circuit_open()

    fake_row = _make_fake_session_row("sess_done", status="EVALUATING")
    mock_db = MagicMock()
    mock_db.execute.return_value.scalar_one_or_none.return_value = fake_row
    mock_session_local.return_value = mock_db

    from orchestrator.session_manager import SessionManager

    sm = SessionManager.__new__(SessionManager)
    sm.state_sync = MagicMock()

    result = sm.mark_session_completed("sess_done", risk_score=0.75)

    assert result is True
    sm.state_sync.get_session_state.assert_not_called()
    sm.state_sync.set_session_state.assert_not_called()

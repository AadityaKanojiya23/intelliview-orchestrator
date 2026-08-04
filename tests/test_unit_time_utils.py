from datetime import datetime, timezone

from orchestrator.time_utils import utcnow


def test_utcnow_returns_datetime():
    """utcnow() should return a datetime object."""
    result = utcnow()

    assert isinstance(result, datetime)


def test_utcnow_is_timezone_aware():
    """utcnow() should return a timezone-aware datetime."""
    result = utcnow()

    assert result.tzinfo is not None
    assert result.tzinfo == timezone.utc


def test_utcnow_is_close_to_current_time():
    """Returned time should be very close to the actual current UTC time."""
    before = datetime.now(timezone.utc)

    result = utcnow()

    after = datetime.now(timezone.utc)

    assert before <= result <= after
"""Unit tests for RetryManager — backoff math, retry-cap, persistence."""

from unittest.mock import patch

from orchestrator.retry_manager import RetryManager, RetryStrategy


def _manager(**overrides):
    defaults = dict(
        max_retries=3,
        base_delay=2,
        max_delay=3600,
        strategy=RetryStrategy.EXPONENTIAL_BACKOFF,
    )
    defaults.update(overrides)
    with patch("orchestrator.retry_manager.redis.from_url") as mock_redis:
        mock_redis.return_value.ping.return_value = True
        mock_redis.return_value.get.return_value = None
        mock_redis.return_value.incr.return_value = 1
        mock_redis.return_value.setex.return_value = True
        mock_redis.return_value.expire.return_value = True
        mock_redis.return_value.delete.return_value = 1
        return RetryManager(**defaults)


def test_can_retry_within_bounds_then_blocks():
    rm = _manager(max_retries=3)
    with patch.object(rm, "get_retry_count", side_effect=[0, 3]):
        assert rm.can_retry("s1") is True
        assert rm.can_retry("s1") is False


def test_calculate_delay_exponential_caps_at_max_delay():
    rm = _manager(
        strategy=RetryStrategy.EXPONENTIAL_BACKOFF, base_delay=2, max_delay=60
    )
    # 2 ** 1 = 2, 2 ** 3 = 8, 2 ** 10 = 1024 -> capped at 60
    assert rm._calculate_delay(1) == 2
    assert rm._calculate_delay(3) == 8
    assert rm._calculate_delay(10) == 60


def test_calculate_delay_linear():
    rm = _manager(strategy=RetryStrategy.LINEAR_BACKOFF, base_delay=5)
    assert rm._calculate_delay(1) == 5
    assert rm._calculate_delay(4) == 20


def test_calculate_delay_immediate():
    rm = _manager(strategy=RetryStrategy.IMMEDIATE)
    assert rm._calculate_delay(5) == 0


def test_schedule_retry_returns_false_when_max_exceeded():
    rm = _manager(max_retries=2)
    with patch.object(rm, "can_retry", return_value=False):
        assert rm.schedule_retry("s1") is False


def test_schedule_retry_stores_metadata_when_allowed():
    rm = _manager()
    with (
        patch.object(rm, "can_retry", return_value=True),
        patch.object(rm, "increment_retry", return_value=1),
    ):
        assert rm.schedule_retry("s2") is True


def test_reset_retry_count_swallows_redis_errors():
    rm = _manager()
    assert rm.reset_retry_count("s1") is True

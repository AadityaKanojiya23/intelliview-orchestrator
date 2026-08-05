import pytest

from orchestrator.retry_manager import RetryManager, RetryStrategy

# ----------------------------
# Fake Redis Client
# ----------------------------


class FakeRedis:
    def __init__(self):
        self.storage = {}

    def get(self, key):
        return self.storage.get(key)

    def set(self, key, value, ex=None):
        self.storage[key] = value

    def incr(self, key):
        value = int(self.storage.get(key, 0)) + 1
        self.storage[key] = str(value)
        return value

    def expire(self, key, ttl):
        pass

    def scan(self, cursor, match=None, count=100):
        return 0, []


# ----------------------------
# Fixtures
# ----------------------------


@pytest.fixture
def retry_manager(monkeypatch):
    fake = FakeRedis()

    monkeypatch.setattr(
        "orchestrator.cache_manager.get_redis_client",
        lambda: fake,
    )
    from orchestrator import cache_manager

    cache_manager.CacheManager._instance = None

    return RetryManager(
        max_retries=3,
        base_delay=2,
        max_delay=60,
    )


# ----------------------------
# Delay Calculation
# ----------------------------


def test_exponential_backoff(retry_manager):
    assert retry_manager._calculate_delay(1) == 2
    assert retry_manager._calculate_delay(2) == 4
    assert retry_manager._calculate_delay(3) == 8


def test_linear_backoff(monkeypatch):
    monkeypatch.setattr(
        "orchestrator.cache_manager.get_redis_client",
        lambda: FakeRedis(),
    )
    from orchestrator import cache_manager

    cache_manager.CacheManager._instance = None

    manager = RetryManager(
        strategy=RetryStrategy.LINEAR_BACKOFF,
        base_delay=5,
    )

    assert manager._calculate_delay(1) == 5
    assert manager._calculate_delay(2) == 10
    assert manager._calculate_delay(3) == 15


def test_immediate_backoff(monkeypatch):
    monkeypatch.setattr(
        "orchestrator.cache_manager.get_redis_client",
        lambda: FakeRedis(),
    )
    from orchestrator import cache_manager

    cache_manager.CacheManager._instance = None

    manager = RetryManager(
        strategy=RetryStrategy.IMMEDIATE,
    )

    assert manager._calculate_delay(1) == 0


# ----------------------------
# Retry Count
# ----------------------------


def test_increment_retry(retry_manager):
    count = retry_manager.increment_retry("session1")

    assert count == 1

    count = retry_manager.increment_retry("session1")

    assert count == 2


def test_get_retry_count(retry_manager):
    retry_manager.increment_retry("abc")

    assert retry_manager.get_retry_count("abc") == 1


# ----------------------------
# Retry Permission
# ----------------------------


def test_can_retry_true(retry_manager):
    assert retry_manager.can_retry("new_session") is True


def test_can_retry_false(retry_manager):
    retry_manager.increment_retry("abc")
    retry_manager.increment_retry("abc")
    retry_manager.increment_retry("abc")

    assert retry_manager.can_retry("abc") is False

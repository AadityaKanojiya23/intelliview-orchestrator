"""Unit tests for the Redis-backed HTTP cache helper."""

from unittest.mock import patch

import orchestrator.http_cache as http_cache


def test_get_returns_none_when_redis_unavailable():
    with patch("orchestrator.http_cache._client", return_value=None):
        assert http_cache.get("anything") is None


def test_set_swallows_redis_errors():
    fake = type("FakeRedis", (), {"set": lambda self, *a, **kw: (_ for _ in ()).throw(Exception("boom"))})()
    with patch("orchestrator.http_cache._client", return_value=fake):
        # Must not raise
        http_cache.set("k", {"v": 1})


def test_get_round_trip():
    class FakeRedis:
        def __init__(self):
            self.store = {}

        def get(self, key):
            return self.store.get(key)

        def set(self, key, value, ex=None):
            self.store[key] = value

        def delete(self, *keys):
            for k in keys:
                self.store.pop(k, None)

        def scan_iter(self, pattern, count=10):
            return [k for k in self.store if k.startswith(pattern.split("*")[0])]

    fake = FakeRedis()
    with patch("orchestrator.http_cache._client", return_value=fake):
        http_cache.set("hello", {"a": 1}, ttl=5)
        assert http_cache.get("hello") == {"a": 1}
        http_cache.invalidate("hello")
        assert http_cache.get("hello") is None


def test_cached_decorator_returns_cached_value():
    calls = {"n": 0}

    @http_cache.cached("counter", ttl=10)
    def expensive():
        calls["n"] += 1
        return {"value": calls["n"]}

    class FakeRedis:
        def __init__(self):
            self.store = {}

        def get(self, key):
            return self.store.get(key)

        def set(self, key, value, ex=None):
            self.store[key] = value

        def delete(self, *keys):
            for k in keys:
                self.store.pop(k, None)

        def scan_iter(self, pattern, count=10):
            return []

    fake = FakeRedis()
    with patch("orchestrator.http_cache._client", return_value=fake):
        assert expensive() == {"value": 1}
        assert expensive() == {"value": 1}
        assert calls["n"] == 1, "decorator should hit the cache on second call"

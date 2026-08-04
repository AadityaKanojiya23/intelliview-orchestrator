import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient

from orchestrator.rate_limiter import RateLimiterMiddleware


# -------------------------
# Fake Redis implementation
# -------------------------

class FakePipeline:
    def __init__(self, count):
        self.count = count

    def zremrangebyscore(self, *args, **kwargs):
        return self

    def zadd(self, *args, **kwargs):
        return self

    def zcard(self, *args, **kwargs):
        return self

    def expire(self, *args, **kwargs):
        return self

    def execute(self):
        return [None, None, self.count, None]


class FakeRedisRaw:
    def __init__(self, count):
        self.count = count

    def pipeline(self, transaction=False):
        return FakePipeline(self.count)


class FakeRedisClient:
    def __init__(self, count):
        self.raw = FakeRedisRaw(count)


# -------------------------
# Helper
# -------------------------

def create_app(monkeypatch, request_count):
    from orchestrator import rate_limiter

    monkeypatch.setattr(
        rate_limiter,
        "get_redis_client",
        lambda: FakeRedisClient(request_count),
    )

    app = FastAPI()

    app.add_middleware(
        RateLimiterMiddleware,
        limit=5,
        window_seconds=60,
    )

    @app.get("/hello")
    async def hello():
        return {"message": "ok"}

    @app.get("/health")
    async def health():
        return {"status": "healthy"}

    return TestClient(app)


# -------------------------
# Tests
# -------------------------

def test_request_allowed(monkeypatch):
    client = create_app(monkeypatch, request_count=3)

    response = client.get("/hello")

    assert response.status_code == 200
    assert response.json() == {"message": "ok"}


def test_rate_limit_exceeded(monkeypatch):
    client = create_app(monkeypatch, request_count=10)

    response = client.get("/hello")

    assert response.status_code == 429
    assert response.json()["detail"] == "Rate limit exceeded"
    assert "Retry-After" in response.headers


def test_health_endpoint_is_exempt(monkeypatch):
    client = create_app(monkeypatch, request_count=100)

    response = client.get("/health")

    assert response.status_code == 200
    assert response.json() == {"status": "healthy"}


def test_client_key_with_api_token():
    from starlette.requests import Request

    scope = {
        "type": "http",
        "headers": [
            (b"x-api-token", b"abc123"),
        ],
        "client": ("127.0.0.1", 5000),
    }

    request = Request(scope)

    key = RateLimiterMiddleware._client_key(request)

    assert key == "127.0.0.1:abc123"


def test_client_key_without_token():
    from starlette.requests import Request

    scope = {
        "type": "http",
        "headers": [],
        "client": ("127.0.0.1", 5000),
    }

    request = Request(scope)

    key = RateLimiterMiddleware._client_key(request)

    assert key == "127.0.0.1:"
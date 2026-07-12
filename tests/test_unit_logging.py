"""
Unit tests for the structured JSON request-logging middleware
(`RequestContextMiddleware` in orchestrator/main.py).

`tests/test_unit_logging.py` only covers the low-level building blocks
(`JsonFormatter` / `log_event`). It never exercises the middleware that
actually wires those helpers into every HTTP request — request-id
generation/propagation, the `request` log event, the `/health` exemption,
and the `unhandled_error` path were previously untested.

These tests build a minimal Starlette app around the real middleware class
(imported straight from `orchestrator.main`) instead of booting the full
FastAPI app, so they stay fast and don't require a live Redis/Postgres
instance.
"""

import io
import json
import logging

import pytest
from starlette.applications import Starlette
from starlette.responses import JSONResponse
from starlette.routing import Route
from starlette.testclient import TestClient

from orchestrator.logging_config import JsonFormatter
from orchestrator.main import RequestContextMiddleware
from orchestrator.main import logger as main_logger


async def _ok(request):
    return JSONResponse({"ok": True})


async def _health(request):
    return JSONResponse({"status": "healthy"})


async def _boom(request):
    raise RuntimeError("kaboom")


def _build_app() -> Starlette:
    app = Starlette(
        routes=[
            Route("/ok", _ok),
            Route("/health", _health),
            Route("/boom", _boom),
        ]
    )
    app.add_middleware(RequestContextMiddleware)
    return app


@pytest.fixture
def client():
    return TestClient(_build_app())


def _request_log_records(caplog):
    return [
        r
        for r in caplog.records
        if r.name == main_logger.name and r.getMessage() == "request"
    ]


def _error_log_records(caplog):
    return [
        r
        for r in caplog.records
        if r.name == main_logger.name and r.getMessage() == "unhandled_error"
    ]


def test_successful_request_emits_structured_request_log(client, caplog):
    with caplog.at_level(logging.INFO, logger=main_logger.name):
        response = client.get("/ok")

    assert response.status_code == 200
    records = _request_log_records(caplog)
    assert len(records) == 1
    record = records[0]
    assert record.method == "GET"
    assert record.path == "/ok"
    assert record.status == 200
    assert isinstance(record.elapsed_ms, float)
    assert record.request_id


def test_response_carries_request_id_and_timing_headers(client):
    response = client.get("/ok")
    assert "X-Request-ID" in response.headers
    assert "X-Response-Time-ms" in response.headers
    # No incoming id supplied -> middleware falls back to uuid4().hex (32 hex chars)
    assert len(response.headers["X-Request-ID"]) == 32


def test_health_path_is_logged_at_debug_not_info(client, caplog):
    # At INFO, /health produces no "request" record (keeps prod logs quiet).
    with caplog.at_level(logging.INFO, logger=main_logger.name):
        response = client.get("/health")
    assert response.status_code == 200
    assert _request_log_records(caplog) == []
    # Still gets request-id/timing headers even though it isn't logged at INFO.
    assert "X-Request-ID" in response.headers
    assert "X-Response-Time-ms" in response.headers

    caplog.clear()

    # At DEBUG, /health is logged like any other request.
    with caplog.at_level(logging.DEBUG, logger=main_logger.name):
        client.get("/health")
    debug_records = [
        r for r in caplog.records if r.name == main_logger.name and r.getMessage() == "request"
    ]
    assert len(debug_records) == 1
    assert debug_records[0].path == "/health"
    assert debug_records[0].levelname == "DEBUG"


def test_valid_incoming_request_id_is_honoured(client):
    response = client.get("/ok", headers={"X-Request-ID": "client-supplied-id-123"})
    assert response.headers["X-Request-ID"] == "client-supplied-id-123"


def test_invalid_incoming_request_id_is_replaced(client):
    bad_id = "not a valid id! (has spaces)"
    response = client.get("/ok", headers={"X-Request-ID": bad_id})
    returned = response.headers["X-Request-ID"]
    assert returned != bad_id
    assert len(returned) == 32  # fell back to a generated uuid4().hex


def test_unhandled_exception_logs_error_event_and_still_raises(client, caplog):
    with caplog.at_level(logging.INFO, logger=main_logger.name):
        with pytest.raises(BaseException) as exc_info:
            client.get("/boom")

    assert "kaboom" in str(exc_info.value)

    error_records = _error_log_records(caplog)
    assert len(error_records) == 1
    assert error_records[0].path == "/boom"
    assert error_records[0].levelname == "ERROR"
    # A failed request must not also emit a successful "request" event.
    assert _request_log_records(caplog) == []


def test_request_log_survives_real_json_serialization():
    """End-to-end: the emitted record round-trips through JsonFormatter
    (the formatter actually used in production), not just pytest's
    LogRecord attribute access."""
    buf = io.StringIO()
    handler = logging.StreamHandler(buf)
    handler.setFormatter(JsonFormatter())
    main_logger.addHandler(handler)
    previous_level = main_logger.level
    main_logger.setLevel(logging.INFO)
    try:
        TestClient(_build_app()).get("/ok")
    finally:
        main_logger.removeHandler(handler)
        main_logger.setLevel(previous_level)

    payloads = [json.loads(line) for line in buf.getvalue().splitlines() if line.strip()]
    request_payloads = [p for p in payloads if p.get("message") == "request"]
    assert len(request_payloads) == 1

    payload = request_payloads[0]
    expected_keys = {"ts", "level", "logger", "message", "request_id", "method", "path", "status", "elapsed_ms"}
    assert expected_keys <= set(payload.keys())
    assert payload["method"] == "GET"
    assert payload["path"] == "/ok"
    assert payload["status"] == 200
    assert payload["level"] == "INFO"

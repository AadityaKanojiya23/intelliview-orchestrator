"""
Tests for the structured logging configuration.
"""

import io
import json
import logging

from orchestrator.logging_config import JsonFormatter, configure_logging, log_event


def test_json_formatter_emits_valid_json():
    formatter = JsonFormatter()
    record = logging.LogRecord(
        name="test",
        level=logging.INFO,
        pathname="x.py",
        lineno=1,
        msg="hello %s",
        args=("world",),
        exc_info=None,
    )
    out = formatter.format(record)
    data = json.loads(out)
    assert data["level"] == "INFO"
    assert data["logger"] == "test"
    assert data["message"] == "hello world"
    assert "ts" in data


def test_json_formatter_includes_extra_fields():
    formatter = JsonFormatter()
    record = logging.LogRecord(
        name="test",
        level=logging.INFO,
        pathname="x.py",
        lineno=1,
        msg="session_completed",
        args=(),
        exc_info=None,
    )
    record.session_id = "abc123"
    record.risk_score = 0.42
    data = json.loads(formatter.format(record))
    assert data["session_id"] == "abc123"
    assert data["risk_score"] == 0.42


def test_log_event_attaches_fields():
    logger = logging.getLogger("test_log_event")
    buf = io.StringIO()
    handler = logging.StreamHandler(buf)
    handler.setFormatter(JsonFormatter())
    logger.addHandler(handler)
    logger.setLevel(logging.INFO)

    log_event(logger, logging.INFO, "session_started", session_id="s1", candidate="c1")
    line = buf.getvalue().strip()
    data = json.loads(line)
    assert data["message"] == "session_started"
    assert data["session_id"] == "s1"
    assert data["candidate"] == "c1"


def test_configure_logging_idempotent(monkeypatch):
    """Calling configure_logging twice doesn't duplicate handlers."""
    monkeypatch.setenv("LOG_LEVEL", "WARNING")
    configure_logging("WARNING")
    root = logging.getLogger()
    n1 = len(root.handlers)
    configure_logging("WARNING")
    n2 = len(root.handlers)
    assert n1 == n2 == 1


def test_json_formatter_handles_exception():
    formatter = JsonFormatter()
    try:
        raise ValueError("boom")
    except ValueError:
        import sys

        record = logging.LogRecord(
            name="t",
            level=logging.ERROR,
            pathname="x.py",
            lineno=1,
            msg="failed",
            args=(),
            exc_info=sys.exc_info(),
        )
    data = json.loads(formatter.format(record))
    assert data["level"] == "ERROR"
    assert "exc" in data
    assert "ValueError" in data["exc"]

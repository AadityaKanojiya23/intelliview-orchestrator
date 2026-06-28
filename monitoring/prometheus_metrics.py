"""
Prometheus Metrics Module

Exposes Prometheus-format metrics for the AI Interview Orchestrator.

Metrics:
- Request count and duration (per method, path, status)
- Session processing (created, completed, failed, risk scores)
- Worker health (registered, healthy, unhealthy, heartbeat age)
- AI pipeline latency (video, audio, evaluation)
- Risk score distribution (histogram buckets)
- System health (Redis, Postgres, queue)
"""

from __future__ import annotations

import logging
import time
from typing import Any

from prometheus_client import (
    CollectorRegistry,
    Counter,
    Gauge,
    Histogram,
    generate_latest,
)

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Registry
# ---------------------------------------------------------------------------

registry = CollectorRegistry()

# ---------------------------------------------------------------------------
# Request metrics
# ---------------------------------------------------------------------------

REQUEST_COUNT = Counter(
    "intelliview_http_requests_total",
    "Total HTTP requests",
    ["method", "path", "status"],
    registry=registry,
)

REQUEST_DURATION = Histogram(
    "intelliview_http_request_duration_seconds",
    "HTTP request duration in seconds",
    ["method", "path"],
    buckets=(0.01, 0.025, 0.05, 0.1, 0.25, 0.5, 1.0, 2.5, 5.0, 10.0),
    registry=registry,
)

# ---------------------------------------------------------------------------
# Session metrics
# ---------------------------------------------------------------------------

SESSIONS_CREATED = Counter(
    "intelliview_sessions_created_total",
    "Total interview sessions created",
    registry=registry,
)

SESSIONS_COMPLETED = Counter(
    "intelliview_sessions_completed_total",
    "Total interview sessions completed",
    registry=registry,
)

SESSIONS_FAILED = Counter(
    "intelliview_sessions_failed_total",
    "Total interview sessions failed",
    registry=registry,
)

SESSIONS_ACTIVE = Gauge(
    "intelliview_sessions_active",
    "Number of currently active sessions",
    registry=registry,
)

SESSION_PROCESSING_DURATION = Histogram(
    "intelliview_session_processing_duration_seconds",
    "Session processing duration in seconds",
    buckets=(1, 5, 10, 30, 60, 120, 300, 600),
    registry=registry,
)

# ---------------------------------------------------------------------------
# Risk score metrics
# ---------------------------------------------------------------------------

RISK_SCORE = Histogram(
    "intelliview_risk_score",
    "Risk score distribution",
    buckets=(0.1, 0.2, 0.3, 0.4, 0.5, 0.6, 0.7, 0.8, 0.9, 1.0),
    registry=registry,
)

# ---------------------------------------------------------------------------
# Worker metrics
# ---------------------------------------------------------------------------

WORKERS_REGISTERED = Gauge(
    "intelliview_workers_registered",
    "Number of registered workers",
    registry=registry,
)

WORKERS_HEALTHY = Gauge(
    "intelliview_workers_healthy",
    "Number of healthy workers",
    registry=registry,
)

WORKERS_UNHEALTHY = Gauge(
    "intelliview_workers_unhealthy",
    "Number of unhealthy workers",
    registry=registry,
)

WORKER_ACTIVE_TASKS = Gauge(
    "intelliview_worker_active_tasks",
    "Active tasks per worker",
    ["worker_id"],
    registry=registry,
)

WORKER_CAPACITY = Gauge(
    "intelliview_worker_capacity",
    "Capacity per worker",
    ["worker_id"],
    registry=registry,
)

WORKER_HEARTBEAT_AGE_SECONDS = Gauge(
    "intelliview_worker_heartbeat_age_seconds",
    "Seconds since last heartbeat per worker",
    ["worker_id"],
    registry=registry,
)

# ---------------------------------------------------------------------------
# AI pipeline latency metrics
# ---------------------------------------------------------------------------

PIPELINE_LATENCY = Histogram(
    "intelliview_pipeline_latency_seconds",
    "AI pipeline stage latency in seconds",
    ["stage"],
    buckets=(0.1, 0.25, 0.5, 1.0, 2.5, 5.0, 10.0, 30.0, 60.0),
    registry=registry,
)

PIPELINE_ERRORS = Counter(
    "intelliview_pipeline_errors_total",
    "Total pipeline errors by stage",
    ["stage", "error_type"],
    registry=registry,
)

# ---------------------------------------------------------------------------
# System health metrics
# ---------------------------------------------------------------------------

REDIS_HEALTH = Gauge(
    "intelliview_redis_health",
    "Redis health (1=healthy, 0=unhealthy)",
    registry=registry,
)

POSTGRES_HEALTH = Gauge(
    "intelliview_postgres_health",
    "Postgres health (1=healthy, 0=unhealthy)",
    registry=registry,
)

QUEUE_DEPTH = Gauge(
    "intelliview_queue_depth",
    "Current Celery queue depth",
    registry=registry,
)

CIRCUIT_BREAKER_STATE = Gauge(
    "intelliview_circuit_breaker_state",
    "Circuit breaker state (0=closed, 1=open, 2=half_open)",
    registry=registry,
)

SYSTEM_UPTIME = Gauge(
    "intelliview_system_uptime_seconds",
    "System uptime in seconds",
    registry=registry,
)

# ---------------------------------------------------------------------------
# Retry / fault metrics
# ---------------------------------------------------------------------------

RETRY_COUNT = Counter(
    "intelliview_retries_total",
    "Total retry attempts",
    registry=registry,
)

FAILURE_COUNT = Counter(
    "intelliview_failures_total",
    "Total failures by type",
    ["failure_type"],
    registry=registry,
)

DLQ_SIZE = Gauge(
    "intelliview_dead_letter_queue_size",
    "Number of sessions in dead letter queue",
    registry=registry,
)


# ---------------------------------------------------------------------------
# Helper functions
# ---------------------------------------------------------------------------


def record_request(method: str, path: str, status: int, duration_seconds: float) -> None:
    """Record a single HTTP request metric."""
    REQUEST_COUNT.labels(method=method, path=path, status=str(status)).inc()
    REQUEST_DURATION.labels(method=method, path=path).observe(duration_seconds)


def record_session_created() -> None:
    SESSIONS_CREATED.inc()


def record_session_completed(duration_seconds: float) -> None:
    SESSIONS_COMPLETED.inc()
    SESSION_PROCESSING_DURATION.observe(duration_seconds)


def record_session_failed() -> None:
    SESSIONS_FAILED.inc()


def record_risk_score(score: float) -> None:
    RISK_SCORE.observe(score)


def record_pipeline_latency(stage: str, duration_seconds: float) -> None:
    PIPELINE_LATENCY.labels(stage=stage).observe(duration_seconds)


def record_pipeline_error(stage: str, error_type: str) -> None:
    PIPELINE_ERRORS.labels(stage=stage, error_type=error_type).inc()


def update_worker_metrics(workers: dict[str, Any]) -> None:
    """Update worker gauges from a workers dict."""
    healthy = 0
    unhealthy = 0
    now = time.time()

    for worker_id, data in workers.items():
        is_healthy = data.get("health_status") == "healthy"
        if is_healthy:
            healthy += 1
        else:
            unhealthy += 1

        WORKER_ACTIVE_TASKS.labels(worker_id=worker_id).set(data.get("active_tasks", 0))
        WORKER_CAPACITY.labels(worker_id=worker_id).set(data.get("capacity", 0))

        last_hb = data.get("last_heartbeat")
        if last_hb:
            try:
                from datetime import datetime

                hb_dt = datetime.fromisoformat(last_hb)
                age = now - hb_dt.timestamp()
                WORKER_HEARTBEAT_AGE_SECONDS.labels(worker_id=worker_id).set(age)
            except (ValueError, TypeError):
                WORKER_HEARTBEAT_AGE_SECONDS.labels(worker_id=worker_id).set(-1)

    WORKERS_REGISTERED.set(len(workers))
    WORKERS_HEALTHY.set(healthy)
    WORKERS_UNHEALTHY.set(unhealthy)


def update_queue_depth(depth: int) -> None:
    QUEUE_DEPTH.set(depth)


def update_system_health(redis_ok: bool, postgres_ok: bool) -> None:
    REDIS_HEALTH.set(1 if redis_ok else 0)
    POSTGRES_HEALTH.set(1 if postgres_ok else 0)


def update_circuit_breaker(state_value: int) -> None:
    """state_value: 0=closed, 1=open, 2=half_open"""
    CIRCUIT_BREAKER_STATE.set(state_value)


def get_metrics_text() -> bytes:
    """Return current metrics in Prometheus text exposition format."""
    return generate_latest(registry)

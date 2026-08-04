"""Health, readiness, and system-diagnostics routes."""

import logging
from datetime import datetime, timezone

from fastapi import APIRouter, HTTPException

from config import ENABLE_PROMETHEUS
from orchestrator.redis_client import circuit_breaker

logger = logging.getLogger(__name__)

APP_START_TIME = datetime.now(timezone.utc)


def create_health_routes(health_monitor, worker_registry, session_manager) -> APIRouter:
    """Create health/readiness/diagnostics routes.

    Args:
        health_monitor: HealthMonitor instance
        worker_registry: WorkerRegistry instance
        session_manager: SessionManager instance

    Returns:
        APIRouter with health routes
    """

    router = APIRouter()

    @router.get("/health")
    async def health_check():
        """
        Health check endpoint
        Returns system status
        """
        uptime = int((datetime.now(timezone.utc) - APP_START_TIME).total_seconds())

        return {
            "alive": True,
            "status": "system running",
            "uptime_seconds": uptime,
            "timestamp": datetime.now(timezone.utc).isoformat(),
        }

    # ========== Deep Health & Probe Endpoints ==========

    @router.get("/livez")
    async def liveness_probe():
        """Kubernetes-style liveness probe. Returns 200 if the process is alive."""
        return health_monitor.liveness_check()

    @router.get("/readyz")
    async def readiness_probe():
        """Kubernetes-style readiness probe. Returns 200 only when all dependencies are up."""
        result = await health_monitor.readiness_check()
        if not result["ready"]:
            from fastapi.responses import JSONResponse as _JSONResponse

            return _JSONResponse(status_code=503, content=result)
        return result

    @router.get("/dependencies")
    async def get_dependency_statuses():
        """Deep health check of all dependencies (Redis, Postgres, Celery broker)."""
        return await health_monitor._check_all_dependencies()

    # ========== Prometheus Metrics Endpoint ==========

    if ENABLE_PROMETHEUS:
        from fastapi.responses import Response as _Response

        from metrics.prometheus_metrics import (
            POSTGRES_HEALTH,
            REDIS_HEALTH,
            WORKERS_HEALTHY,
            WORKERS_REGISTERED,
            WORKERS_UNHEALTHY,
            get_metrics_text,
        )

        @router.get("/metrics")
        async def prometheus_metrics():
            """Prometheus metrics endpoint."""
            # Dynamic check of dependency statuses
            deps = await health_monitor._check_all_dependencies()
            REDIS_HEALTH.set(1 if deps.get("redis", {}).get("status") == "healthy" else 0)
            POSTGRES_HEALTH.set(1 if deps.get("postgres", {}).get("status") == "healthy" else 0)

            # Worker status gauges
            all_workers = worker_registry.get_all_workers()
            unhealthy = worker_registry.detect_unhealthy_workers()
            WORKERS_REGISTERED.set(len(all_workers))
            WORKERS_HEALTHY.set(len(all_workers) - len(unhealthy))
            WORKERS_UNHEALTHY.set(len(unhealthy))

            return _Response(
                content=get_metrics_text(),
                media_type="text/plain; version=0.0.4; charset=utf-8",
            )

    @router.get("/circuit-breaker")
    async def get_circuit_breaker_status():
        """Return the current state of the Redis circuit breaker."""
        return {
            "state": circuit_breaker.state.value,
            "failure_count": circuit_breaker._failure_count,
            "failure_threshold": circuit_breaker.failure_threshold,
            "cooldown_seconds": circuit_breaker.cooldown_seconds,
            "timestamp": datetime.now(timezone.utc).isoformat(),
        }

    @router.get("/system-health")
    async def get_system_health():
        """
        Get comprehensive system health status

        Performs health checks on:
        - Redis connectivity
        - Worker nodes
        - Active sessions
        - Queue backlog

        Returns:
            dict: System health status and metrics
        """
        try:
            logger.debug("Performing system health check")

            return health_monitor.check_system_health(
                worker_registry=worker_registry, session_manager=session_manager
            )

        except Exception as e:
            logger.error(f"Error checking system health: {e!s}")
            raise HTTPException(status_code=500, detail=f"Error checking system health: {e!s}")

    @router.get("/worker-health")
    async def get_worker_health():
        """
        Get detailed health status of all workers

        Returns:
            dict: Worker health information
        """
        try:
            logger.debug("Fetching worker health status")

            return health_monitor.check_worker_health(worker_registry)

        except Exception as e:
            logger.error(f"Error fetching worker health: {e!s}")
            raise HTTPException(status_code=500, detail=f"Error fetching worker health: {e!s}")

    return router

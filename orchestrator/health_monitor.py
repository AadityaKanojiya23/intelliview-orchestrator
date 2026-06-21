"""
Health Monitor Module

Continuously monitors system and worker health to detect failures early.

Responsibilities:
- Detect inactive/unhealthy workers
- Detect stuck/failed sessions
- Monitor queue backlog
- Trigger alerts and recovery actions
"""

import json
import logging
from datetime import datetime, timezone
from typing import Any

import redis

from config import REDIS_URL

logger = logging.getLogger(__name__)


class HealthStatus(str):
    """Health status indicators"""

    HEALTHY = "healthy"
    DEGRADED = "degraded"
    UNHEALTHY = "unhealthy"
    CRITICAL = "critical"


class HealthMonitor:
    """
    Monitors system and component health to detect failures and trigger recovery.

    Monitors:
    - Worker node heartbeats and responsiveness
    - Session processing timeouts
    - Queue backlog and delays
    - System resource utilization
    """

    def __init__(
        self,
        redis_url: str = REDIS_URL,
        heartbeat_timeout: int = 60,
        session_timeout: int = 1800,
        queue_threshold: int = 1000,
    ):
        """
        Initialize HealthMonitor

        Args:
            redis_url: Redis connection URL
            heartbeat_timeout: Seconds without heartbeat to mark worker unhealthy (default: 60)
            session_timeout: Seconds in PROCESSING state to mark stuck (default: 1800 = 30 min)
            queue_threshold: Queue size threshold for alerting (default: 1000)
        """
        self.redis_url = redis_url
        self.heartbeat_timeout = heartbeat_timeout
        self.session_timeout = session_timeout
        self.queue_threshold = queue_threshold
        self.redis_client = self._connect_redis()
        self.health_status_key = "system:health_status"
        self.last_check_key = "system:last_health_check"

        logger.info(
            f"HealthMonitor initialized: heartbeat_timeout={heartbeat_timeout}s, "
            f"session_timeout={session_timeout}s, queue_threshold={queue_threshold}"
        )

    def _connect_redis(self) -> redis.Redis | None:
        """Connect to Redis server"""
        try:
            client = redis.from_url(self.redis_url, decode_responses=True)
            client.ping()
            logger.info("Connected to Redis for health monitoring")
            return client
        except Exception as e:
            logger.error(f"Failed to connect to Redis: {e!s}")
            return None

    def check_system_health(self, worker_registry=None, session_manager=None) -> dict[str, Any]:
        """
        Perform comprehensive system health check

        Args:
            worker_registry: Optional WorkerRegistry instance for worker checks
            session_manager: Optional SessionManager instance for session checks

        Returns:
            Dict with health status and detailed metrics
        """
        try:
            logger.debug("Performing comprehensive system health check")

            health_status = {
                "timestamp": datetime.now(timezone.utc).isoformat(),
                "overall_status": HealthStatus.HEALTHY,
                "components": {},
            }

            # Check Redis connectivity
            redis_status = self._check_redis_health()
            health_status["components"]["redis"] = redis_status
            if redis_status["status"] != HealthStatus.HEALTHY:
                health_status["overall_status"] = HealthStatus.CRITICAL

            # Check workers if registry provided
            if worker_registry:
                worker_status = self.check_worker_health(worker_registry)
                health_status["components"]["workers"] = worker_status
                if (
                    worker_status["status"]
                    in [
                        HealthStatus.CRITICAL,
                        HealthStatus.UNHEALTHY,
                    ]
                    and health_status["overall_status"] != HealthStatus.CRITICAL
                ):
                    health_status["overall_status"] = worker_status["status"]

            # Check sessions if manager provided
            if session_manager:
                session_status = self.check_session_health(session_manager)
                health_status["components"]["sessions"] = session_status
                if (
                    session_status["status"]
                    in [
                        HealthStatus.CRITICAL,
                        HealthStatus.DEGRADED,
                    ]
                    and health_status["overall_status"] == HealthStatus.HEALTHY
                ):
                    health_status["overall_status"] = session_status["status"]

            # Check queue backlog
            queue_status = self.check_queue_health()
            health_status["components"]["queue"] = queue_status
            if queue_status["status"] == HealthStatus.CRITICAL:
                health_status["overall_status"] = HealthStatus.CRITICAL
            elif queue_status["status"] == HealthStatus.DEGRADED:
                if health_status["overall_status"] == HealthStatus.HEALTHY:
                    health_status["overall_status"] = HealthStatus.DEGRADED

            # Store health status
            if self.redis_client:
                self.redis_client.set(
                    self.health_status_key,
                    json.dumps(health_status),
                    ex=300,
                )
                self.redis_client.set(self.last_check_key, datetime.now(timezone.utc).isoformat())

            logger.info(f"System health check complete: {health_status['overall_status']}")

            return health_status

        except Exception as e:
            logger.error(f"Error checking system health: {e!s}")
            return {
                "timestamp": datetime.now(timezone.utc).isoformat(),
                "overall_status": HealthStatus.UNHEALTHY,
                "error": str(e),
            }

    def check_worker_health(self, worker_registry) -> dict[str, Any]:
        """
        Check health of all workers

        Args:
            worker_registry: WorkerRegistry instance to check

        Returns:
            Dict with worker health status
        """
        try:
            logger.debug("Checking worker health")

            all_workers = worker_registry.get_all_workers()
            unhealthy_workers = worker_registry.detect_unhealthy_workers()

            total = len(all_workers)
            healthy = total - len(unhealthy_workers)

            status = HealthStatus.HEALTHY
            if len(unhealthy_workers) > total * 0.5:  # > 50% unhealthy
                status = HealthStatus.CRITICAL
            elif len(unhealthy_workers) > 0:  # Any unhealthy
                status = HealthStatus.DEGRADED

            return {
                "status": status,
                "total_workers": total,
                "healthy_workers": healthy,
                "unhealthy_workers": len(unhealthy_workers),
                "unhealthy_list": unhealthy_workers[:10],
                "availability_percent": (healthy / total * 100) if total > 0 else 0,
            }

        except Exception as e:
            logger.error(f"Error checking worker health: {e!s}")
            return {"status": HealthStatus.UNHEALTHY, "error": str(e)}

    def check_session_health(self, session_manager) -> dict[str, Any]:
        """
        Check health of active sessions (detect stuck sessions)

        Args:
            session_manager: SessionManager instance to check

        Returns:
            Dict with session health status
        """
        try:
            logger.debug("Checking session health")

            # Get sessions stuck in PROCESSING
            stuck_sessions = []
            active_sessions = (
                session_manager.get_active_sessions()
                if hasattr(session_manager, "get_active_sessions")
                else []
            )

            for session in active_sessions:
                if session.get("status") == "PROCESSING":
                    start_time = session.get("start_time")
                    if start_time:
                        try:
                            start_dt = datetime.fromisoformat(start_time)
                            elapsed = (datetime.now(timezone.utc) - start_dt).total_seconds()

                            if elapsed > self.session_timeout:
                                stuck_sessions.append(
                                    {
                                        "session_id": session.get("session_id"),
                                        "elapsed_seconds": elapsed,
                                    }
                                )
                        except Exception:
                            pass

            status = HealthStatus.HEALTHY
            if len(stuck_sessions) > len(active_sessions) * 0.25:  # > 25% stuck
                status = HealthStatus.CRITICAL
            elif len(stuck_sessions) > 0:  # Any stuck
                status = HealthStatus.DEGRADED

            return {
                "status": status,
                "total_active": len(active_sessions),
                "stuck_sessions": len(stuck_sessions),
                "stuck_list": stuck_sessions[:5],
                "max_processing_time": max([s.get("elapsed_seconds", 0) for s in stuck_sessions], default=0),
            }

        except Exception as e:
            logger.error(f"Error checking session health: {e!s}")
            return {"status": HealthStatus.UNHEALTHY, "error": str(e)}

    def check_queue_health(self) -> dict[str, Any]:
        """
        Check Redis queue backlog and health

        Returns:
            Dict with queue health status
        """
        try:
            logger.debug("Checking queue health")

            if not self.redis_client:
                return {
                    "status": HealthStatus.UNHEALTHY,
                    "error": "Redis not available",
                }

            # Get queue lengths
            queue_length = self.redis_client.llen("celery_queue") if self.redis_client else 0

            status = HealthStatus.HEALTHY
            if queue_length > self.queue_threshold:
                status = HealthStatus.CRITICAL
            elif queue_length > self.queue_threshold * 0.7:
                status = HealthStatus.DEGRADED

            return {
                "status": status,
                "queue_length": queue_length,
                "threshold": self.queue_threshold,
                "backlog_percent": (queue_length / self.queue_threshold * 100)
                if self.queue_threshold > 0
                else 0,
            }

        except Exception as e:
            logger.error(f"Error checking queue health: {e!s}")
            return {"status": HealthStatus.UNHEALTHY, "error": str(e)}

    def _check_redis_health(self) -> dict[str, Any]:
        """
        Check Redis connectivity and responsiveness

        Returns:
            Dict with Redis health status
        """
        try:
            if not self.redis_client:
                return {
                    "status": HealthStatus.UNHEALTHY,
                    "error": "Redis client not initialized",
                }

            # Test ping
            self.redis_client.ping()

            # Get some basic info
            info = self.redis_client.info()
            connected_clients = info.get("connected_clients", 0)
            used_memory = info.get("used_memory_human", "unknown")

            return {
                "status": HealthStatus.HEALTHY,
                "connected": True,
                "clients": connected_clients,
                "memory": used_memory,
            }

        except Exception as e:
            logger.error(f"Error checking Redis health: {e!s}")
            return {"status": HealthStatus.UNHEALTHY, "error": str(e)}

    def detect_worker_failures(self, worker_registry) -> list[str]:
        """
        Identify workers that appear to have failed

        Args:
            worker_registry: WorkerRegistry instance

        Returns:
            List of worker_ids that appear to have failed
        """
        try:
            logger.debug("Detecting worker failures")
            failed_workers = worker_registry.detect_unhealthy_workers()

            if failed_workers:
                logger.warning(f"Detected {len(failed_workers)} failed workers: {failed_workers}")

            return failed_workers

        except Exception as e:
            logger.error(f"Error detecting worker failures: {e!s}")
            return []

    def detect_stuck_sessions(self, session_manager) -> list[str]:
        """
        Identify sessions stuck in PROCESSING state

        Args:
            session_manager: SessionManager instance

        Returns:
            List of session_ids that appear stuck
        """
        try:
            logger.debug("Detecting stuck sessions")

            stuck_sessions = []
            active_sessions = (
                session_manager.get_active_sessions()
                if hasattr(session_manager, "get_active_sessions")
                else []
            )

            for session in active_sessions:
                if session.get("status") == "PROCESSING":
                    start_time = session.get("start_time")
                    if start_time:
                        try:
                            start_dt = datetime.fromisoformat(start_time)
                            elapsed = (datetime.now(timezone.utc) - start_dt).total_seconds()

                            if elapsed > self.session_timeout:
                                stuck_sessions.append(session.get("session_id"))
                                logger.warning(
                                    f"Detected stuck session {session.get('session_id')}: "
                                    f"{elapsed}s processing"
                                )
                        except Exception:
                            pass

            return stuck_sessions

        except Exception as e:
            logger.error(f"Error detecting stuck sessions: {e!s}")
            return []

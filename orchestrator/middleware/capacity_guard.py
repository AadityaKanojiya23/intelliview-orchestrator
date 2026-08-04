"""
Graceful Degradation Middleware

Returns HTTP 503 Service Unavailable when every registered worker is
either unhealthy or at full capacity (see Scheduler.can_accept_task /
WorkerRegistry.get_available_workers), instead of accepting a request
that has nowhere to be processed.
"""

from fastapi import Request
from fastapi.responses import JSONResponse
from starlette.middleware.base import BaseHTTPMiddleware

# Only guard endpoints that actually dispatch work to a worker.
# Read-only/status endpoints must stay reachable even when saturated,
# so operators/dashboards can still see what's going on.
GUARDED_PATH_PREFIXES = ("/start-interview",)

RETRY_AFTER_SECONDS = 5


class CapacityGuardMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        if request.url.path.startswith(GUARDED_PATH_PREFIXES):
            # Imported lazily, inside dispatch, to avoid a circular import
            # (main.py imports this middleware module at load time).
            from orchestrator.main import scheduler

            try:
                accept = scheduler.can_accept_task()
            except Exception:
                # If the capacity check itself fails (e.g. Redis down),
                # fail safe by treating the system as unavailable rather
                # than silently letting the request through.
                accept = False

            if not accept:
                return JSONResponse(
                    status_code=503,
                    headers={"Retry-After": str(RETRY_AFTER_SECONDS)},
                    content={
                        "error": "service_unavailable",
                        "message": (
                            "All workers are currently unhealthy or at "
                            "maximum processing capacity. Please retry shortly."
                        ),
                        "retry_after_seconds": RETRY_AFTER_SECONDS,
                    },
                )
        return await call_next(request)

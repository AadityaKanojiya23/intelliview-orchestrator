"""
Contract tests: assert that every endpoint advertised in README.md and the
module spec .md files is actually exposed by the FastAPI app, with the
documented HTTP method.

These are static checks (no live server required).
"""

import pytest
from fastapi import FastAPI

from orchestrator.main import app


def _all_routes(application: FastAPI):
    out = []

    def _walk(routes, prefix=""):
        for r in routes:
            # FastAPI's include_router() wraps included routers in a lazy
            # `_IncludedRouter` node that has no `.path`/`.methods` of its
            # own — recurse into its wrapped router to reach the real routes.
            original_router = getattr(r, "original_router", None)
            if original_router is not None:
                sub_prefix = (
                    getattr(getattr(r, "include_context", None), "prefix", "") or ""
                )
                _walk(original_router.routes, prefix + sub_prefix)
                continue
            methods = getattr(r, "methods", None) or set()
            path = getattr(r, "path", None) or getattr(r, "path_format", None)
            if path:
                for m in methods:
                    if m in {"GET", "POST", "PUT", "DELETE", "PATCH"}:
                        out.append((m, prefix + path))

    _walk(application.routes)
    return out


# Endpoints documented in README.md / module .md files.
EXPECTED = {
    ("GET", "/health"),
    ("GET", "/dashboard"),
    ("POST", "/start-interview"),
    ("GET", "/session-status/{session_id}"),
    ("GET", "/active-sessions"),
    ("GET", "/completed-sessions"),
    ("GET", "/failed-sessions"),
    ("GET", "/stuck-sessions"),
    ("GET", "/session-statistics"),
    ("GET", "/worker-distribution"),
    ("GET", "/high-risk-sessions"),
    ("GET", "/cache-stats"),
    ("POST", "/sync-to-database"),
    ("DELETE", "/clear-cache"),
    ("POST", "/register-worker"),
    ("POST", "/worker/heartbeat"),
    ("GET", "/workers"),
    ("GET", "/worker-statistics"),
    ("GET", "/load-status"),
    ("GET", "/scheduling-status"),
    ("POST", "/switch-strategy"),
    ("DELETE", "/deregister-worker/{worker_id}"),
    ("POST", "/retry-session/{session_id}"),
    ("GET", "/system-health"),
    ("GET", "/worker-health"),
    ("GET", "/admin/fairness-audit"),
    ("GET", "/recovery-queue"),
    ("GET", "/failure-log"),
    ("GET", "/dead-letter-queue"),
    ("GET", "/fault-statistics"),
    ("POST", "/detect-failures"),
    ("GET", "/interviews/{session_id}/report"),
}


@pytest.mark.parametrize(("method", "path"), sorted(EXPECTED))
def test_endpoint_exists(method, path):
    routes = _all_routes(app)
    assert (method, path) in routes, f"Missing endpoint {method} {path}"

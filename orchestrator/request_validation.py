"""
Request Validation Middleware

Provides input sanitization, request size limits, and content-type
validation for the FastAPI application.
"""

from __future__ import annotations

import logging
import re
from collections.abc import Callable

from fastapi import Request, Response
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.responses import JSONResponse

logger = logging.getLogger(__name__)

# Patterns that indicate potential injection or abuse
_DANGEROUS_PATTERNS = [
    re.compile(r"<script", re.IGNORECASE),
    re.compile(r"javascript:", re.IGNORECASE),
    re.compile(r"on\w+\s*=", re.IGNORECASE),
    re.compile(r"union\s+select", re.IGNORECASE),
    re.compile(r";\s*drop\s+table", re.IGNORECASE),
    re.compile(r"__import__", re.IGNORECASE),
    re.compile(r"eval\s*\(", re.IGNORECASE),
    re.compile(r"exec\s*\(", re.IGNORECASE),
]

# Content types we accept for body-bearing methods
_ALLOWED_CONTENT_TYPES = frozenset(
    {
        "application/json",
        "application/x-www-form-urlencoded",
        "multipart/form-data",
        "text/plain",
    }
)

# Methods that should have a body
_BODY_METHODS = frozenset({"POST", "PUT", "PATCH", "DELETE"})


class RequestValidationMiddleware(BaseHTTPMiddleware):
    """Validates incoming requests for size, content-type, and dangerous payloads."""

    def __init__(
        self,
        app,
        max_body_size_bytes: int = 1024 * 1024,  # 1 MB default
        check_content_type: bool = True,
        scan_for_dangerous_patterns: bool = True,
    ) -> None:
        super().__init__(app)
        self.max_body_size_bytes = max_body_size_bytes
        self.check_content_type = check_content_type
        self.scan_for_dangerous_patterns = scan_for_dangerous_patterns

    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        path = request.url.path

        # Skip validation for health probes and docs
        if path in ("/health", "/ready", "/livez", "/docs", "/openapi.json"):
            return await call_next(request)

        # Content-type validation for body-bearing methods
        if self.check_content_type and request.method in _BODY_METHODS:
            content_type = request.headers.get("content-type", "")
            if content_type:
                base_type = content_type.split(";")[0].strip().lower()
                if base_type not in _ALLOWED_CONTENT_TYPES:
                    return JSONResponse(
                        status_code=415,
                        content={"detail": f"Unsupported content-type: {base_type}"},
                    )

        # Request size limit
        content_length = request.headers.get("content-length")
        if content_length:
            try:
                size = int(content_length)
                if size > self.max_body_size_bytes:
                    return JSONResponse(
                        status_code=413,
                        content={
                            "detail": f"Request body too large ({size} bytes, max {self.max_body_size_bytes})"
                        },
                    )
            except ValueError:
                pass

        # Scan query params and path for dangerous patterns
        if self.scan_for_dangerous_patterns:
            check_target = f"{request.url.path}?{request.url.query}"
            for pattern in _DANGEROUS_PATTERNS:
                if pattern.search(check_target):
                    logger.warning(
                        "Blocked suspicious request pattern: path=%s ip=%s",
                        path,
                        request.client.host if request.client else "unknown",
                    )
                    return JSONResponse(
                        status_code=400,
                        content={"detail": "Request contains invalid characters or patterns"},
                    )

        return await call_next(request)

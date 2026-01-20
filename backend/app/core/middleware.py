"""HTTP middleware for request logging and monitoring."""

import time
import uuid
from typing import Callable

from fastapi import Request, Response
from starlette.middleware.base import BaseHTTPMiddleware

from app.core.logging import get_logger

logger = get_logger(__name__)

# Paths to exclude from logging (health checks, static files)
EXCLUDED_PATHS = {"/health", "/api/health", "/api/docs", "/api/redoc", "/api/openapi.json"}


class RequestLoggingMiddleware(BaseHTTPMiddleware):
    """Middleware to log all HTTP requests with timing information.

    Logs include:
    - Request ID for correlation
    - HTTP method and path
    - Response status code
    - Request duration in milliseconds
    - Client IP address

    Excludes:
    - Health check endpoints (to avoid log spam)
    - Static file requests
    - Sensitive headers (Authorization, Cookie)
    """

    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        # Skip logging for excluded paths
        if request.url.path in EXCLUDED_PATHS:
            return await call_next(request)

        # Generate request ID for correlation
        request_id = str(uuid.uuid4())[:8]

        # Extract client info
        client_ip = request.client.host if request.client else "unknown"
        method = request.method
        path = request.url.path
        query = str(request.url.query) if request.url.query else None

        # Log request start
        logger.info(
            "http.request.start",
            request_id=request_id,
            method=method,
            path=path,
            query=query,
            client_ip=client_ip,
        )

        # Process request and measure duration
        start_time = time.perf_counter()
        try:
            response = await call_next(request)
            duration_ms = (time.perf_counter() - start_time) * 1000

            # Log request completion
            logger.info(
                "http.request.complete",
                request_id=request_id,
                method=method,
                path=path,
                status_code=response.status_code,
                duration_ms=round(duration_ms, 2),
            )

            # Add request ID to response headers for debugging
            response.headers["X-Request-ID"] = request_id
            return response

        except Exception as exc:
            duration_ms = (time.perf_counter() - start_time) * 1000

            # Log request error
            logger.error(
                "http.request.error",
                request_id=request_id,
                method=method,
                path=path,
                duration_ms=round(duration_ms, 2),
                error=str(exc),
            )
            raise

"""Request logging middleware."""
import time

from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request

from app.core.logging import get_logger

logger = get_logger(__name__)


class RequestLogMiddleware(BaseHTTPMiddleware):
    """Middleware that logs all requests."""

    async def dispatch(self, request: Request, call_next):
        """Log request and response."""
        start_time = time.time()
        correlation_id = getattr(request.state, "correlation_id", "unknown")

        logger.info(
            "request_started",
            method=request.method,
            path=request.url.path,
            correlation_id=correlation_id,
        )

        response = await call_next(request)

        duration_ms = (time.time() - start_time) * 1000
        logger.info(
            "request_completed",
            method=request.method,
            path=request.url.path,
            status_code=response.status_code,
            duration_ms=round(duration_ms, 2),
            correlation_id=correlation_id,
        )

        return response

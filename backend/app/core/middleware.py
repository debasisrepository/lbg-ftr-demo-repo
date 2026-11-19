"""Core middleware: correlation ID tracking"""
import uuid

from fastapi import Request
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.responses import Response


class CorrelationIDMiddleware(BaseHTTPMiddleware):
    """Add correlation ID to each request"""

    async def dispatch(self, request: Request, call_next):
        # Get correlation ID from header or generate new one
        correlation_id = request.headers.get("X-Correlation-ID") or str(uuid.uuid4())

        # Store in request state for access by route handlers
        request.state.correlation_id = correlation_id

        # Process request
        response: Response = await call_next(request)

        # Add correlation ID to response headers
        response.headers["X-Correlation-ID"] = correlation_id

        return response


def get_correlation_id(request: Request) -> str:
    """Get correlation ID from request state"""
    return getattr(request.state, "correlation_id", str(uuid.uuid4()))

"""
Correlation middleware for request tracing.
Requirement: REQ-OBS-001
"""
import uuid

from fastapi import Request
from starlette.middleware.base import BaseHTTPMiddleware


class CorrelationMiddleware(BaseHTTPMiddleware):
    """Middleware to ensure every request has a correlation ID."""
    
    async def dispatch(self, request: Request, call_next):
        # Get correlation ID from header or generate new one
        correlation_id = request.headers.get("X-Correlation-ID")
        
        if not correlation_id or len(correlation_id) > 64:
            correlation_id = str(uuid.uuid4())
        
        # Store in request state for access by route handlers
        request.state.correlation_id = correlation_id
        
        # Process request
        response = await call_next(request)
        
        # Echo correlation ID in response
        response.headers["X-Correlation-ID"] = correlation_id
        
        return response


def get_correlation_id(request: Request) -> str:
    """Get correlation ID from request state."""
    return getattr(request.state, "correlation_id", str(uuid.uuid4()))

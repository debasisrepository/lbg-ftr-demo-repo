"""Correlation ID helpers for request tracing."""
from fastapi import Request


def get_correlation_id(request: Request) -> str:
    """Get correlation ID from request state."""
    return getattr(request.state, "correlation_id", "unknown")

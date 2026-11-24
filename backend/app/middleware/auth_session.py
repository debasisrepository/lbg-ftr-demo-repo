"""Authentication session middleware."""
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request


class BearerCaptureMiddleware(BaseHTTPMiddleware):
    """Middleware that captures bearer token to request state."""

    async def dispatch(self, request: Request, call_next):
        """Extract bearer token from Authorization header."""
        auth_header = request.headers.get("Authorization", "")
        token = None

        if auth_header.startswith("Bearer "):
            token = auth_header[7:]  # Strip "Bearer " prefix

        request.state.bearer_token = token
        return await call_next(request)

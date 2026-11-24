"""Error response shape middleware."""
from fastapi import Request
from fastapi.responses import JSONResponse

from app.core.errors import (
    AppError,
    AuthenticationError,
    AuthorizationError,
    ConflictError,
    NotFoundError,
    RateLimitError,
    ValidationError,
)
from app.core.logging import get_logger

logger = get_logger(__name__)


async def error_shape_middleware(request: Request, call_next):
    """Convert exceptions to consistent error shape."""
    try:
        return await call_next(request)
    except AppError as exc:
        # Map exception types to status codes
        status_code_map = {
            AuthenticationError: 401,
            AuthorizationError: 403,
            NotFoundError: 404,
            ConflictError: 409,
            ValidationError: 422,
            RateLimitError: 429,
        }
        status_code = status_code_map.get(type(exc), 400)

        correlation_id = getattr(request.state, "correlation_id", "unknown")

        logger.error(
            "app_error",
            error_type=type(exc).__name__,
            error_code=exc.code,
            message=exc.message,
            status_code=status_code,
            correlation_id=correlation_id,
        )

        return JSONResponse(
            status_code=status_code,
            content={
                "error": {
                    "code": exc.code,
                    "message": exc.message,
                    "details": exc.details,
                }
            },
        )
    except Exception as exc:
        correlation_id = getattr(request.state, "correlation_id", "unknown")

        logger.exception(
            "unhandled_exception",
            error_type=type(exc).__name__,
            correlation_id=correlation_id,
        )

        return JSONResponse(
            status_code=500,
            content={
                "error": {
                    "code": "internal_error",
                    "message": "An internal error occurred",
                    "details": {},
                }
            },
        )

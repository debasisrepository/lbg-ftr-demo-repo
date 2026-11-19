"""Application exception hierarchy and error handlers"""
from fastapi import HTTPException, Request, status
from fastapi.responses import JSONResponse


class AppError(Exception):
    """Base application error"""
    def __init__(self, message: str, status_code: int = status.HTTP_400_BAD_REQUEST):
        self.message = message
        self.status_code = status_code
        super().__init__(message)


class AuthenticationError(AppError):
    """Authentication failed"""
    def __init__(self, message: str = "Authentication failed"):
        super().__init__(message, status.HTTP_401_UNAUTHORIZED)


class AuthorizationError(AppError):
    """Not authorized to perform action"""
    def __init__(self, message: str = "Not authorized"):
        super().__init__(message, status.HTTP_403_FORBIDDEN)


class ResourceNotFoundError(AppError):
    """Resource not found"""
    def __init__(self, message: str = "Resource not found"):
        super().__init__(message, status.HTTP_404_NOT_FOUND)


class RateLimitError(AppError):
    """Rate limit exceeded"""
    def __init__(self, message: str = "Too many requests"):
        super().__init__(message, status.HTTP_429_TOO_MANY_REQUESTS)


class ValidationError(AppError):
    """Validation error"""
    def __init__(self, message: str):
        super().__init__(message, status.HTTP_400_BAD_REQUEST)


async def app_error_handler(request: Request, exc: AppError) -> JSONResponse:
    """Handle application errors"""
    return JSONResponse(
        status_code=exc.status_code,
        content={"detail": exc.message}
    )


async def http_exception_handler(request: Request, exc: HTTPException) -> JSONResponse:
    """Handle FastAPI HTTP exceptions"""
    return JSONResponse(
        status_code=exc.status_code,
        content={"detail": exc.detail}
    )


async def generic_exception_handler(request: Request, exc: Exception) -> JSONResponse:
    """Handle unexpected exceptions"""
    # Log the error but don't leak internals to client
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={"detail": "An internal error occurred"}
    )

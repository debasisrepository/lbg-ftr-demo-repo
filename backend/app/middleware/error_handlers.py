"""
Global error handlers for standardized error responses.
Requirement: API Specification section 1.6
"""
from fastapi import Request, status
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from sqlalchemy.exc import OperationalError


async def validation_exception_handler(request: Request, exc: RequestValidationError):
    """Handle Pydantic validation errors with 422 status."""
    correlation_id = getattr(request.state, "correlation_id", "unknown")
    
    errors = []
    for error in exc.errors():
        field = ".".join(str(loc) for loc in error["loc"] if loc != "body")
        errors.append({
            "field": field,
            "message": error["msg"]
        })
    
    return JSONResponse(
        status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
        content={
            "detail": "Validation error",
            "status_code": status.HTTP_422_UNPROCESSABLE_ENTITY,
            "error_code": "validation_error",
            "correlation_id": correlation_id,
            "errors": errors
        }
    )


async def database_exception_handler(request: Request, exc: OperationalError):
    """Handle database connection errors with 503 status."""
    correlation_id = getattr(request.state, "correlation_id", "unknown")
    
    return JSONResponse(
        status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
        content={
            "detail": "Database unavailable",
            "status_code": status.HTTP_503_SERVICE_UNAVAILABLE,
            "error_code": "dependency_unavailable",
            "correlation_id": correlation_id
        }
    )


async def generic_exception_handler(request: Request, exc: Exception):
    """Handle unexpected errors with 500 status, no internals leaked."""
    correlation_id = getattr(request.state, "correlation_id", "unknown")
    
    # Log the actual error internally (would go to structlog in production)
    import traceback
    print(f"Internal error [{correlation_id}]: {exc!s}")
    traceback.print_exc()
    
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={
            "detail": "An unexpected error occurred",
            "status_code": status.HTTP_500_INTERNAL_SERVER_ERROR,
            "error_code": "internal_error",
            "correlation_id": correlation_id
        }
    )

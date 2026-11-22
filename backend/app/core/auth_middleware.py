"""Global authentication middleware (H-001 remediation)"""
import uuid

from fastapi import Request, Response
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.responses import JSONResponse

from .errors import AuthorizationError
from .security import decode_jwt_token

# Public routes that don't require authentication
PUBLIC_ROUTES = {
    "/",
    "/api/v1/docs",
    "/api/v1/redoc",
    "/api/v1/openapi.json",
    "/api/v1/health",
    "/api/v1/health/",
    "/api/v1/health/liveness",
    "/api/v1/health/readiness",
    "/api/v1/auth/sign-in",
    "/api/v1/auth/submit-proof",
    "/api/v1/auth/step-up",
    "/api/v1/auth/verify-step-up",
    "/api/v1/auth/start-recovery",
}


class AuthenticationMiddleware(BaseHTTPMiddleware):
    """
    Global authentication middleware that validates JWT tokens.
    
    This middleware:
    - Extracts and validates JWT tokens from Authorization header
    - Stores authenticated context in request.state for downstream use
    - Maintains an explicit allowlist of public routes
    - Prevents authentication bypass vulnerabilities
    """
    
    async def dispatch(self, request: Request, call_next):
        # Skip authentication for public routes
        if request.url.path in PUBLIC_ROUTES:
            return await call_next(request)
        
        # Check for Authorization header
        auth_header = request.headers.get("Authorization")
        if not auth_header:
            return JSONResponse(
                status_code=401,
                content={"detail": "Missing authorization header"}
            )
        
        if not auth_header.startswith("Bearer "):
            return JSONResponse(
                status_code=401,
                content={"detail": "Invalid authorization header format"}
            )
        
        # Extract and validate token
        token = auth_header.split(" ")[1]
        
        try:
            payload = decode_jwt_token(token)
        except AuthorizationError as e:
            return JSONResponse(
                status_code=401,
                content={"detail": str(e)}
            )
        except Exception:
            return JSONResponse(
                status_code=401,
                content={"detail": "Invalid authentication token"}
            )
        
        # Store authenticated context in request.state
        try:
            request.state.customer_id = uuid.UUID(payload["sub"])
            request.state.session_id = uuid.UUID(payload["session_id"])
            request.state.active_profile_id = uuid.UUID(payload["active_profile_id"]) if payload.get("active_profile_id") else None
        except (KeyError, ValueError) as e:
            return JSONResponse(
                status_code=401,
                content={"detail": f"Invalid token payload: {str(e)}"}
            )
        
        # Continue with request
        response = await call_next(request)
        return response


def get_current_customer_id(request: Request) -> uuid.UUID:
    """
    Dependency to extract customer ID from authenticated request state.
    
    This should be used with FastAPI's Depends() in route handlers.
    The middleware guarantees this value exists for protected routes.
    """
    if not hasattr(request.state, "customer_id"):
        raise AuthorizationError("Authentication required")
    return request.state.customer_id


def get_current_session_id(request: Request) -> uuid.UUID:
    """
    Dependency to extract session ID from authenticated request state.
    """
    if not hasattr(request.state, "session_id"):
        raise AuthorizationError("Authentication required")
    return request.state.session_id


def get_current_profile_id(request: Request) -> uuid.UUID | None:
    """
    Dependency to extract active profile ID from authenticated request state.
    Returns None if no profile is active.
    """
    if not hasattr(request.state, "active_profile_id"):
        raise AuthorizationError("Authentication required")
    return request.state.active_profile_id

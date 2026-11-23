"""
Authentication router for sign-in and session management endpoints.
Requirement: FR-AUTH-003, FR-AUTH-006
Endpoints: E-01, E-02, E-03
"""
from typing import Annotated

from fastapi import APIRouter, Depends, Request, status
from sqlalchemy.orm import Session

from app.database import get_db
from app.middleware.auth_middleware import security
from app.middleware.correlation_middleware import get_correlation_id
from app.schemas.auth_schemas import LoginRequest, LoginResponse, SessionResponse
from app.services.auth_service import AuthService

router = APIRouter(tags=["Authentication"])


def get_client_address(request: Request) -> str:
    """Extract client IP address from request."""
    # In production, this would handle X-Forwarded-For from API gateway
    return request.client.host if request.client else "unknown"


@router.post(
    "/auth/login",
    response_model=LoginResponse,
    status_code=status.HTTP_200_OK,
    summary="Passcode sign-in",
    description="E-01: Sign in with passcode on a registered device"
)
def login(
    request_body: LoginRequest,
    request: Request,
    db: Annotated[Session, Depends(get_db)],
    correlation_id: Annotated[str, Depends(get_correlation_id)]
):
    """
    E-01: POST /api/v1/auth/login — passcode sign-in
    
    Sign-in is available only on a previously registered eligible device.
    Incorrect passcode entry does not grant access.
    Successful passcode entry transitions the customer into the authenticated app experience.
    Sign-in failures display clear and accessible feedback without disclosing sensitive security internals.
    
    Returns:
        LoginResponse with bearer token and session details
    
    Raises:
        401: Sign-in failed (generic message for all failure causes)
        422: Validation error
        429: Rate limit exceeded
        503: CIAM unavailable
    """
    auth_service = AuthService(db)
    client_address = get_client_address(request)
    
    return auth_service.login(
        request=request_body,
        client_address=client_address,
        correlation_id=correlation_id
    )


@router.get(
    "/auth/session",
    response_model=SessionResponse,
    status_code=status.HTTP_200_OK,
    summary="Session validation",
    description="E-02: Validate current session and extend activity"
)
def get_session(
    request: Request,
    db: Annotated[Session, Depends(get_db)],
    correlation_id: Annotated[str, Depends(get_correlation_id)],
    credentials = Depends(security)
):
    """
    E-02: GET /api/v1/auth/session — session validation
    
    Used by RequireAuth and auth-context before any protected content is shown.
    A live session counts as activity and extends the inactivity window.
    
    Returns:
        SessionResponse with session details
    
    Raises:
        401: Session invalid, expired, or revoked
        503: CIAM unavailable
    """
    auth_service = AuthService(db)
    
    return auth_service.validate_session(
        token=credentials.credentials,
        correlation_id=correlation_id
    )


@router.post(
    "/auth/logout",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="End session",
    description="E-03: Logout and revoke session"
)
def logout(
    request: Request,
    db: Annotated[Session, Depends(get_db)],
    correlation_id: Annotated[str, Depends(get_correlation_id)],
    credentials = Depends(security)
):
    """
    E-03: POST /api/v1/auth/logout — end the session
    
    Revokes the session so the token can no longer be used.
    
    Returns:
        204 No Content
    
    Raises:
        401: Session invalid or already revoked
    """
    auth_service = AuthService(db)
    
    auth_service.logout(
        token=credentials.credentials,
        correlation_id=correlation_id
    )

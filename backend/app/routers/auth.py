"""Auth router."""
from fastapi import APIRouter, Depends, Request
from sqlalchemy.orm import Session

from app.core.clock import Clock
from app.core.deps import get_clock, get_correlation_id, get_db
from app.schemas.auth_schemas import (
    LoginRequest,
    LogoutResponse,
    RoleContextSchema,
    SessionResponse,
    TokenResponse,
    UserSchema,
)
from app.services.auth_service import AuthService
from app.services.role_profile_service import RoleProfileService

router = APIRouter()


@router.post("/login", response_model=TokenResponse)
def login(
    request: Request,
    body: LoginRequest,
    db: Session = Depends(get_db),
    clock: Clock = Depends(get_clock),
    correlation_id: str = Depends(get_correlation_id),
):
    """Login and create session."""
    auth_service = AuthService(db, clock)
    role_service = RoleProfileService(db)

    # Get client IP
    client_ip = request.client.host if request.client else "unknown"

    # Login (will need to determine initial active role)
    # For MVP, get user's first available role
    user = auth_service.user_repo.get_by_username(body.username)
    if user:
        available_roles = role_service.get_available_roles(str(user.id))
        if not available_roles:
            from app.core.errors import AuthorizationError
            raise AuthorizationError("User has no assigned roles", code="no_roles")

        active_role_code = available_roles[0].role_code
    else:
        from app.core.errors import AuthenticationError
        raise AuthenticationError("Invalid credentials", code="invalid_credentials")

    token, session = auth_service.login(
        username=body.username,
        password=body.password,
        active_role_code=active_role_code,
        client_ip=client_ip,
        correlation_id=correlation_id,
    )

    # Build response
    return TokenResponse(
        access_token=token,
        token_type="Bearer",
        expires_in=int((session.expires_at - session.issued_at).total_seconds()),
        inactivity_timeout_seconds=session.inactivity_timeout_seconds,
        session_id=str(session.id),
        user=UserSchema(
            user_id=str(user.id),
            username=user.username,
            display_name=user.display_name,
            email=user.email,
        ),
        active_role_code=session.active_role_code,
        available_roles=[
            RoleContextSchema(
                role_code=r.role_code,
                role_label=r.role_label,
                allowed_widgets=r.allowed_widgets,
                entitled_queue_states=r.entitled_queue_states,
                allowed_actions=r.allowed_actions,
                can_view_sensitive_fields=r.can_view_sensitive_fields,
            )
            for r in available_roles
        ],
    )


@router.post("/logout", response_model=LogoutResponse)
def logout(
    request: Request,
    db: Session = Depends(get_db),
    clock: Clock = Depends(get_clock),
    correlation_id: str = Depends(get_correlation_id),
):
    """Logout and revoke session."""
    auth_service = AuthService(db, clock)

    token = getattr(request.state, "bearer_token", None)
    if not token:
        from app.core.errors import AuthenticationError
        raise AuthenticationError("No token provided", code="no_token")

    session = auth_service.logout(token, correlation_id)

    return LogoutResponse(
        session_id=str(session.id),
        revoked_at=session.revoked_at,
    )


@router.get("/session", response_model=SessionResponse)
def get_session(
    request: Request,
    db: Session = Depends(get_db),
    clock: Clock = Depends(get_clock),
):
    """Get current session info."""
    auth_service = AuthService(db, clock)
    role_service = RoleProfileService(db)

    token = getattr(request.state, "bearer_token", None)
    if not token:
        from app.core.errors import AuthenticationError
        raise AuthenticationError("No token provided", code="no_token")

    user, session = auth_service.validate_token(token)
    available_roles = role_service.get_available_roles(str(user.id))

    # Calculate seconds until inactivity timeout
    now = clock.now()
    seconds_since_activity = (now - session.last_activity_at).total_seconds()
    seconds_until_timeout = max(0, session.inactivity_timeout_seconds - seconds_since_activity)

    return SessionResponse(
        session_id=str(session.id),
        user=UserSchema(
            user_id=str(user.id),
            username=user.username,
            display_name=user.display_name,
            email=user.email,
        ),
        active_role_code=session.active_role_code,
        available_roles=[
            RoleContextSchema(
                role_code=r.role_code,
                role_label=r.role_label,
                allowed_widgets=r.allowed_widgets,
                entitled_queue_states=r.entitled_queue_states,
                allowed_actions=r.allowed_actions,
                can_view_sensitive_fields=r.can_view_sensitive_fields,
            )
            for r in available_roles
        ],
        issued_at=session.issued_at,
        expires_at=session.expires_at,
        seconds_until_inactivity_timeout=int(seconds_until_timeout),
    )

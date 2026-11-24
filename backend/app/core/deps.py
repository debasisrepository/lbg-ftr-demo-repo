"""FastAPI dependencies for database session, auth, and request context."""
import uuid
from typing import Annotated

from fastapi import Depends, Request
from sqlalchemy.orm import Session

from app.core.clock import Clock, clock
from app.core.context import RequestContext
from app.core.db import SessionLocal
from app.core.errors import AuthenticationError, AuthorizationError


def get_db() -> Session:  # type: ignore
    """Get database session."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def get_clock() -> Clock:
    """Get clock instance for dependency injection."""
    return clock


def get_correlation_id(request: Request) -> str:
    """Get correlation ID from request state."""
    return getattr(request.state, "correlation_id", str(uuid.uuid4()))


def get_request_context(request: Request, db: Annotated[Session, Depends(get_db)]) -> RequestContext:
    """Get request context with authenticated user and role."""
    # Get bearer token
    token = getattr(request.state, "bearer_token", None)
    if not token:
        raise AuthenticationError("No token provided", code="no_token")

    # Validate token
    from app.services.auth_service import AuthService
    from app.services.role_profile_service import RoleProfileService

    auth_service = AuthService(db, get_clock())
    role_service = RoleProfileService(db)

    user, session = auth_service.validate_token(token)

    # Resolve role
    active_role = role_service.resolve(str(user.id), session.active_role_code)
    available_roles = role_service.get_available_roles(str(user.id))

    return RequestContext(
        user_id=str(user.id),
        username=user.username,
        display_name=user.display_name,
        email=user.email,
        session_id=str(session.id),
        active_role=active_role,
        available_roles=available_roles,
        correlation_id=getattr(request.state, "correlation_id", str(uuid.uuid4())),
    )


def require_action(action: str):
    """Dependency factory for action-based authorization."""

    def _check_action(ctx: Annotated[RequestContext, Depends(get_request_context)]) -> RequestContext:
        """Check if user's active role allows the action."""
        if not ctx.active_role.can(action):
            raise AuthorizationError(
                f"Action '{action}' not allowed for role '{ctx.active_role.role_code}'",
                code="forbidden_action"
            )
        return ctx

    return Depends(_check_action)

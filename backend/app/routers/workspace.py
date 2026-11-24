"""Workspace router."""
from typing import Optional
from fastapi import APIRouter, Depends, Request
from sqlalchemy.orm import Session

from app.core.clock import Clock
from app.core.context import RequestContext
from app.core.deps import get_clock, get_db, get_request_context
from app.repositories.session_repository import SessionRepository
from app.schemas.workspace_schemas import (
    ActiveRoleRequest,
    ActiveRoleResponse,
    LandingResponse,
)
from app.services.role_profile_service import RoleProfileService
from app.services.workspace_service import WorkspaceService

router = APIRouter()


@router.get(
    "/landing",
    response_model=LandingResponse,
    operation_id="get_workspace_landing",
    summary="Get Landing Workspace",
    description="Return the landing payload for the active role with widgets and actions.",
)
def get_landing(
    request: Request,
    role_code: Optional[str] = None,
    db: Session = Depends(get_db),
    clock: Clock = Depends(get_clock),
    ctx: RequestContext = Depends(get_request_context),
):
    """Get landing workspace for active role.
    
    Args:
        role_code: Optional role code parameter (for compatibility; currently ignored
                   as the active role is determined from the session)
    """
    workspace_service = WorkspaceService(db, clock)

    payload = workspace_service.build_landing_payload(
        role=ctx.active_role,
        available_roles=ctx.available_roles,
        user_id=ctx.user_id,
    )

    return LandingResponse(**payload)


@router.put("/active-role", response_model=ActiveRoleResponse)
def switch_active_role(
    request: Request,
    body: ActiveRoleRequest,
    db: Session = Depends(get_db),
    clock: Clock = Depends(get_clock),
    ctx: RequestContext = Depends(get_request_context),
):
    """Switch active role."""
    role_service = RoleProfileService(db)
    session_repo = SessionRepository(db)

    # Verify user has requested role
    has_role = any(r.role_code == body.role_code for r in ctx.available_roles)
    if not has_role:
        from app.core.errors import AuthorizationError
        raise AuthorizationError(
            f"User does not have role {body.role_code}",
            code="forbidden_role",
        )

    # Get session and update role
    token = getattr(request.state, "bearer_token", None)
    if not token:
        from app.core.errors import AuthenticationError
        raise AuthenticationError("No token provided", code="no_token")

    from app.core.security import hash_token
    token_hash = hash_token(token)
    session = session_repo.get_by_token_hash(token_hash)

    if not session:
        from app.core.errors import AuthenticationError
        raise AuthenticationError("Session not found", code="session_invalid")

    previous_role_code = session.active_role_code
    session_repo.update_role(session, body.role_code)
    db.commit()

    # Get new role context
    new_role = role_service.resolve(ctx.user_id, body.role_code)

    return ActiveRoleResponse(
        previous_role_code=previous_role_code,
        active_role_code=body.role_code,
        allowed_actions=new_role.allowed_actions,
        switched_at=clock.now(),
    )

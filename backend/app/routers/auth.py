from fastapi import APIRouter, Depends, Request, status
from sqlalchemy.orm import Session
from app.database import get_db
from app.schemas.auth_schemas import LoginRequest, TokenResponse, LogoutResponse
from app.services.auth_service import AuthService
from app.middleware.auth_context import get_current_user, get_current_session
from app.models.auth import UserIdentity, AuthSession
from app.common.correlation import get_correlation_id
from app.config import settings
from app.common.errors import AuthenticationError, RateLimitError


router = APIRouter(prefix="/auth", tags=["Authentication"])


@router.post("/login", response_model=TokenResponse, status_code=status.HTTP_200_OK)
def login(
    request: Request,
    login_data: LoginRequest,
    db: Session = Depends(get_db)
):
    """
    Authenticate user with username and password.
    
    Returns JWT access token and session information.
    Step-up authentication required after initial login.
    """
    correlation_id = get_correlation_id(request)
    client_ip = request.client.host if request.client else "unknown"
    
    auth_service = AuthService(db, correlation_id)
    
    try:
        access_token, session_id, active_profile_id = auth_service.login(
            username=login_data.username,
            password=login_data.password,
            client_ip=client_ip
        )
        
        # Get available step-up methods
        user = auth_service.auth_repo.get_user_by_username(login_data.username)
        available_methods = auth_service.get_available_sca_methods(user.id)
        
        return TokenResponse(
            access_token=access_token,
            token_type="Bearer",
            expires_in_seconds=settings.jwt_expiry_minutes * 60,
            session_id=session_id,
            step_up_required=True,
            available_step_up_methods=available_methods,
            active_profile_id=active_profile_id,
            user={
                "id": user.id,
                "username": user.username,
                "status": user.status
            }
        )
    except (AuthenticationError, RateLimitError):
        raise


@router.post("/logout", response_model=LogoutResponse, status_code=status.HTTP_200_OK)
def logout(
    request: Request,
    current_user: UserIdentity = Depends(get_current_user),
    current_session: AuthSession = Depends(get_current_session),
    db: Session = Depends(get_db)
):
    """
    Logout user and revoke session.
    
    Requires valid Bearer token.
    """
    correlation_id = get_correlation_id(request)
    
    auth_service = AuthService(db, correlation_id)
    auth_service.logout(current_session.id, current_user.id)
    
    return LogoutResponse(message="Logged out successfully")

"""Profile router."""
from fastapi import APIRouter, Depends, HTTPException, Request
from sqlalchemy.orm import Session
from app.database import get_db
from app.middleware.auth_context import get_current_user, get_current_session
from app.schemas.profile_schemas import ProfileListResponse, ActivateProfileRequest, ActiveProfileResponse
from app.services.entitlement_service import EntitlementService
from app.repositories.profile_repository import ProfileRepository
from app.common.correlation import get_correlation_id
from app.models.auth import UserIdentity, AuthSession


router = APIRouter(prefix="/profiles", tags=["profiles"])


@router.get("", response_model=ProfileListResponse)
def get_profiles(
    request: Request,
    current_user: UserIdentity = Depends(get_current_user),
    current_session: AuthSession = Depends(get_current_session),
    db: Session = Depends(get_db)
):
    """Get list of profiles with entitlements for current user."""
    correlation_id = get_correlation_id(request)
    
    # Get entitled profiles
    entitlement_service = EntitlementService(db)
    profiles = entitlement_service.get_entitled_profiles(current_user.id)
    
    return ProfileListResponse(
        active_profile_id=current_session.active_profile_id,
        profiles=profiles
    )


@router.post("/activate", response_model=ActiveProfileResponse)
def activate_profile(
    request: Request,
    activate_request: ActivateProfileRequest,
    current_user: UserIdentity = Depends(get_current_user),
    current_session: AuthSession = Depends(get_current_session),
    db: Session = Depends(get_db)
):
    """Activate a profile for the current session."""
    correlation_id = get_correlation_id(request)
    
    # Check profile access
    entitlement_service = EntitlementService(db)
    if not entitlement_service.check_profile_access(activate_request.profile_id, current_user.id):
        raise HTTPException(status_code=403, detail="Access denied to this profile")
    
    # Update session active profile
    profile_repo = ProfileRepository(db)
    profile_repo.update_active_profile(current_session.id, activate_request.profile_id)
    
    # Get profile details
    profile = profile_repo.get_profile_by_id(activate_request.profile_id)
    if not profile:
        raise HTTPException(status_code=404, detail="Profile not found")
    
    return ActiveProfileResponse(
        profile_id=profile.id,
        profile_type=profile.profile_type,
        display_name=profile.display_name
    )

"""
Profiles router for profile switching and business accounts.
Requirement: BR-ACCT-002, BR-ACCT-003, BR-ACCT-010, ADR-003
Release 2: Profile management and business accounts
"""

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.database import get_db
from app.middleware.auth_middleware import get_current_user
from app.middleware.correlation_middleware import get_correlation_id
from app.models.customer_profile_ref import CustomerProfileRef
from app.schemas.profiles_schemas import (
    BusinessAccountsResponse,
    ProfilesResponse,
    SwitchProfileRequest,
    SwitchProfileResponse,
)
from app.services.profile_service import ProfileService

router = APIRouter()


@router.get("/", response_model=ProfilesResponse)
def get_profiles(
    db: Session = Depends(get_db),
    current_user: CustomerProfileRef = Depends(get_current_user),
    correlation_id: str = Depends(get_correlation_id)
) -> ProfilesResponse:
    """
    GET /api/v1/profiles - Get all profiles for authenticated identity.
    
    Per ADR-003: One identity, many profiles.
    Per BRL-ACCT-03: Show profile only if user has at least one active entitlement.
    
    Returns profiles with at least one active entitlement.
    
    Returns:
        ProfilesResponse with profiles and active_profile_id
    
    Raises:
        401: Invalid or expired session
    """
    profile_service = ProfileService(db)
    
    return profile_service.get_profiles(
        identity_reference=current_user.ciam_subject_reference,
        active_profile_id=current_user.id
    )


@router.post("/switch", response_model=SwitchProfileResponse)
def switch_profile(
    request: SwitchProfileRequest,
    db: Session = Depends(get_db),
    current_user: CustomerProfileRef = Depends(get_current_user),
    correlation_id: str = Depends(get_correlation_id)
) -> SwitchProfileResponse:
    """
    POST /api/v1/profiles/switch - Switch active profile without re-authentication.
    
    Per ADR-003: Profile switching without sign-in.
    Per BRL-ACCT-03: Requires at least one active entitlement on target profile.
    
    Request body:
        { "profile_id": "uuid" }
    
    Returns:
        SwitchProfileResponse with new active profile details
    
    Raises:
        401: Invalid or expired session
        403: Not entitled to access target profile
        404: Profile not found
    """
    profile_service = ProfileService(db)
    
    return profile_service.switch_profile(
        profile_id=request.profile_id,
        identity_reference=current_user.ciam_subject_reference
    )


@router.get("/business/accounts", response_model=BusinessAccountsResponse)
def get_business_accounts(
    db: Session = Depends(get_db),
    current_user: CustomerProfileRef = Depends(get_current_user),
    correlation_id: str = Depends(get_correlation_id)
) -> BusinessAccountsResponse:
    """
    GET /api/v1/profiles/business/accounts - Get business accounts for active business profile.
    
    Per BR-ACCT-010: Business account overview with business name, available balance,
    and pending outgoing payments.
    
    Returns:
        BusinessAccountsResponse with business accounts
    
    Raises:
        401: Invalid or expired session
        404: Not a business profile
    """
    profile_service = ProfileService(db)
    
    return profile_service.get_business_accounts(
        customer_id=current_user.id
    )

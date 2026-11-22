"""Profile router"""
import uuid

from fastapi import APIRouter, Depends, Request
from sqlalchemy.orm import Session

from app.core.auth_middleware import get_current_customer_id, get_current_session_id
from app.core.errors import ResourceNotFoundError
from app.database import get_db
from app.schemas.profile_schemas import (
    ProfileListResponse,
    ProfileOut,
    SetActiveProfileRequest,
    SetActiveProfileResponse,
)
from app.services.profile_service import ProfileService

router = APIRouter(prefix="/profiles", tags=["profiles"])


@router.get("", response_model=ProfileListResponse)
def get_profiles(
    customer_id: uuid.UUID = Depends(get_current_customer_id),
    db: Session = Depends(get_db)
):
    """Get all profiles for authenticated customer"""

    profile_service = ProfileService()
    profiles = profile_service.get_profiles_for_customer(db, customer_id)

    # Convert to response DTOs
    profile_outs = [
        ProfileOut(
            profile_id=p.profile_id,
            customer_id=p.customer_id,
            profile_type=p.profile_type,
            display_name=p.display_name,
            status=p.status,
            entitlements=[
                {
                    "entitlement_id": e.entitlement_id,
                    "profile_id": e.profile_id,
                    "entitlement_code": e.entitlement_code,
                    "capability_type": e.capability_type,
                    "can_view_accounts": e.can_view_accounts,
                    "can_manage_payees": e.can_manage_payees,
                    "can_initiate_payments": e.can_initiate_payments,
                    "effective_from": e.effective_from,
                    "effective_to": e.effective_to,
                }
                for e in p.entitlements
            ]
        )
        for p in profiles
    ]

    return ProfileListResponse(profiles=profile_outs)


@router.put("/active", response_model=SetActiveProfileResponse)
def set_active_profile(
    request_body: SetActiveProfileRequest,
    customer_id: uuid.UUID = Depends(get_current_customer_id),
    session_id: uuid.UUID = Depends(get_current_session_id),
    db: Session = Depends(get_db)
):
    """Set active profile for session"""

    profile_service = ProfileService()

    # Set active profile
    profile_service.set_active_profile(
        db=db,
        session_id=session_id,
        customer_id=customer_id,
        profile_id=request_body.profile_id
    )

    db.commit()

    # Get profile details for response
    profile = profile_service.get_profile_by_id(db, request_body.profile_id)

    if not profile:
        raise ResourceNotFoundError("Profile not found")

    return SetActiveProfileResponse(
        profile_id=profile.profile_id,
        display_name=profile.display_name,
        message="Active profile updated"
    )

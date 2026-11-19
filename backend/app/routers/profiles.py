"""Profile router"""
import uuid

from fastapi import APIRouter, Depends, Request
from sqlalchemy.orm import Session

from app.core.errors import AuthorizationError, ResourceNotFoundError
from app.core.security import decode_jwt_token
from app.database import get_db
from app.schemas.profile_schemas import (
    ProfileListResponse,
    ProfileOut,
    SetActiveProfileRequest,
    SetActiveProfileResponse,
)
from app.services.profile_service import ProfileService

router = APIRouter(prefix="/profiles", tags=["profiles"])


def get_current_customer_id(request: Request) -> uuid.UUID:
    """Extract customer ID from JWT token"""
    auth_header = request.headers.get("Authorization")
    if not auth_header or not auth_header.startswith("Bearer "):
        raise AuthorizationError("Missing or invalid authorization header")

    token = auth_header.split(" ")[1]
    payload = decode_jwt_token(token)

    customer_id_str = payload.get("sub")
    if not customer_id_str:
        raise AuthorizationError("Invalid token: missing subject")

    return uuid.UUID(customer_id_str)


def get_session_id(request: Request) -> uuid.UUID:
    """Extract session ID from JWT token"""
    auth_header = request.headers.get("Authorization")
    if not auth_header or not auth_header.startswith("Bearer "):
        raise AuthorizationError("Missing or invalid authorization header")

    token = auth_header.split(" ")[1]
    payload = decode_jwt_token(token)

    session_id_str = payload.get("session_id")
    if not session_id_str:
        raise AuthorizationError("Invalid token: missing session_id")

    return uuid.UUID(session_id_str)


@router.get("", response_model=ProfileListResponse)
def get_profiles(
    request: Request,
    db: Session = Depends(get_db)
):
    """Get all profiles for authenticated customer"""
    customer_id = get_current_customer_id(request)

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
    request: Request,
    db: Session = Depends(get_db)
):
    """Set active profile for session"""
    customer_id = get_current_customer_id(request)
    session_id = get_session_id(request)

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

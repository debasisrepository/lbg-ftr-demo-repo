"""Payee router."""
from fastapi import APIRouter, Depends, HTTPException, Query, Request
from sqlalchemy.orm import Session
from app.database import get_db
from app.middleware.auth_context import get_current_user, get_current_session
from app.schemas.payee_schemas import (
    PayeeListResponse,
    CreatePayeeRequest,
    PayeeResponse,
    CoPOverrideRequest
)
from app.services.payee_service import PayeeService
from app.services.entitlement_service import EntitlementService
from app.common.correlation import get_correlation_id
from app.common.errors import AuthorizationError, ValidationError
from app.models.auth import UserIdentity, AuthSession


router = APIRouter(prefix="/payees", tags=["payees"])


@router.get("", response_model=PayeeListResponse)
def get_payees(
    request: Request,
    profile_id: int = Query(..., description="Profile ID"),
    current_user: UserIdentity = Depends(get_current_user),
    current_session: AuthSession = Depends(get_current_session),
    db: Session = Depends(get_db)
):
    """Get payee list for a profile."""
    correlation_id = get_correlation_id(request)
    
    # Check profile access
    entitlement_service = EntitlementService(db)
    if not entitlement_service.check_profile_access(profile_id, current_user.id):
        raise HTTPException(status_code=403, detail="Access denied to this profile")
    
    # Get payees
    payee_service = PayeeService(db, correlation_id)
    payees = payee_service.get_payees(profile_id)
    
    return PayeeListResponse(payees=payees)


@router.post("", response_model=PayeeResponse)
def create_payee(
    request: Request,
    payee_request: CreatePayeeRequest,
    current_user: UserIdentity = Depends(get_current_user),
    current_session: AuthSession = Depends(get_current_session),
    db: Session = Depends(get_db)
):
    """Create a new payee with fresh payee-action SCA and CoP check."""
    correlation_id = get_correlation_id(request)
    
    # Check profile access
    entitlement_service = EntitlementService(db)
    if not entitlement_service.check_profile_access(payee_request.profile_id, current_user.id):
        raise HTTPException(status_code=403, detail="Access denied to this profile")
    
    # Create payee with SCA and CoP
    payee_service = PayeeService(db, correlation_id)
    try:
        payee = payee_service.create_payee(
            profile_id=payee_request.profile_id,
            display_name=payee_request.display_name,
            nickname=payee_request.nickname,
            sort_code=payee_request.sort_code,
            account_number=payee_request.account_number,
            payee_action_challenge_id=payee_request.payee_action_challenge_id,
            payee_action_assertion=payee_request.payee_action_assertion
        )
    except AuthorizationError as e:
        raise HTTPException(status_code=403, detail=str(e))
    except ValidationError as e:
        raise HTTPException(status_code=422, detail=str(e))
    
    return PayeeResponse(**payee)


@router.post("/{payee_id}/confirm-warning", response_model=PayeeResponse)
def confirm_cop_warning(
    request: Request,
    payee_id: int,
    override_request: CoPOverrideRequest,
    current_user: UserIdentity = Depends(get_current_user),
    current_session: AuthSession = Depends(get_current_session),
    db: Session = Depends(get_db)
):
    """Confirm CoP warning and allow proceeding with payee."""
    correlation_id = get_correlation_id(request)
    
    # Confirm warning
    payee_service = PayeeService(db, correlation_id)
    try:
        result = payee_service.confirm_cop_warning(payee_id, override_request.override_reason)
    except ValidationError as e:
        raise HTTPException(status_code=422, detail=str(e))
    
    # Return updated payee info
    return PayeeResponse(
        payee_id=result["payee_id"],
        display_name="",  # Not returned in confirmation
        sort_code="",  # Not returned in confirmation
        masked_account_number="",  # Not returned in confirmation
        cop_result=result["cop_result"],
        warning_message=None,
        can_proceed=result["can_proceed"],
        override_required=False
    )

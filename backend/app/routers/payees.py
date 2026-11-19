"""Payees router"""
import uuid

from fastapi import APIRouter, Depends, Request
from sqlalchemy.orm import Session

from app.core.errors import AuthorizationError
from app.core.security import decode_jwt_token
from app.database import get_db
from app.schemas.payee_schemas import (
    AcknowledgeCopRequest,
    AcknowledgeCopResponse,
    CopCheckOut,
    CreatePayeeRequest,
    CreatePayeeResponse,
    PayeeListResponse,
    PayeeOut,
    RunCopCheckRequest,
    RunCopCheckResponse,
    UpdatePayeeRequest,
    UpdatePayeeResponse,
)
from app.services.cop_service import CopService
from app.services.entitlement_service import EntitlementService
from app.services.payee_service import PayeeService

router = APIRouter(prefix="/payees", tags=["payees"])


def get_current_customer_and_profile(request: Request) -> tuple[uuid.UUID, uuid.UUID]:
    """Extract customer ID and active profile ID from JWT token"""
    auth_header = request.headers.get("Authorization")
    if not auth_header or not auth_header.startswith("Bearer "):
        raise AuthorizationError("Missing or invalid authorization header")

    token = auth_header.split(" ")[1]
    payload = decode_jwt_token(token)

    customer_id_str = payload.get("sub")
    if not customer_id_str:
        raise AuthorizationError("Invalid token: missing subject")

    profile_id_str = payload.get("active_profile_id")
    if not profile_id_str:
        raise AuthorizationError("Invalid token: no active profile")

    return uuid.UUID(customer_id_str), uuid.UUID(profile_id_str)


def payee_to_out(payee) -> PayeeOut:
    """Convert Payee model to PayeeOut DTO"""
    # Get latest CoP check
    latest_cop = None
    if payee.cop_checks:
        sorted_checks = sorted(payee.cop_checks, key=lambda c: c.checked_at, reverse=True)
        if sorted_checks:
            cop = sorted_checks[0]
            latest_cop = CopCheckOut(
                cop_check_id=cop.cop_check_id,
                outcome=cop.outcome,
                suggested_name=cop.suggested_name,
                policy_treatment=cop.policy_treatment,
                checked_at=cop.checked_at,
                expires_at=cop.expires_at,
                customer_acknowledged_at=cop.customer_acknowledged_at,
            )

    return PayeeOut(
        payee_id=payee.payee_id,
        customer_id=payee.customer_id,
        profile_id=payee.profile_id,
        payee_name=payee.payee_name,
        sort_code=payee.sort_code,
        account_number_masked=payee.account_number_masked,
        payee_type=payee.payee_type,
        is_saved=payee.is_saved,
        status=payee.status,
        last_verified_at=payee.last_verified_at,
        latest_cop_check=latest_cop,
    )


@router.get("", response_model=PayeeListResponse)
def get_payees(
    request: Request,
    db: Session = Depends(get_db)
):
    """Get payees for authenticated customer and active profile"""
    customer_id, profile_id = get_current_customer_and_profile(request)

    # Check entitlement
    entitlement_service = EntitlementService()
    entitlement_service.require_capability(db, profile_id, "manage_payees")

    # Get payees
    payee_service = PayeeService()
    payees = payee_service.get_payees_for_customer(db, customer_id, profile_id)

    payee_outs = [payee_to_out(p) for p in payees]

    return PayeeListResponse(payees=payee_outs)


@router.post("", response_model=CreatePayeeResponse)
def create_payee(
    request_body: CreatePayeeRequest,
    request: Request,
    db: Session = Depends(get_db)
):
    """Create new payee with CoP check"""
    customer_id, profile_id = get_current_customer_and_profile(request)

    # Check entitlement
    entitlement_service = EntitlementService()
    entitlement_service.require_capability(db, profile_id, "manage_payees")

    # Create payee
    payee_service = PayeeService()
    payee, cop_check = payee_service.create_payee(
        db=db,
        customer_id=customer_id,
        profile_id=profile_id,
        payee_name=request_body.payee_name,
        sort_code=request_body.sort_code,
        account_number=request_body.account_number,
        payee_type=request_body.payee_type,
    )

    db.commit()

    return CreatePayeeResponse(
        payee=payee_to_out(payee),
        cop_check=CopCheckOut(
            cop_check_id=cop_check.cop_check_id,
            outcome=cop_check.outcome,
            suggested_name=cop_check.suggested_name,
            policy_treatment=cop_check.policy_treatment,
            checked_at=cop_check.checked_at,
            expires_at=cop_check.expires_at,
            customer_acknowledged_at=cop_check.customer_acknowledged_at,
        )
    )


@router.get("/{payee_id}", response_model=PayeeOut)
def get_payee(
    payee_id: uuid.UUID,
    request: Request,
    db: Session = Depends(get_db)
):
    """Get payee by ID"""
    customer_id, profile_id = get_current_customer_and_profile(request)

    # Check entitlement
    entitlement_service = EntitlementService()
    entitlement_service.require_capability(db, profile_id, "manage_payees")

    # Get payee
    payee_service = PayeeService()
    payee = payee_service.get_payee_by_id(db, payee_id, customer_id)

    return payee_to_out(payee)


@router.put("/{payee_id}", response_model=UpdatePayeeResponse)
def update_payee(
    payee_id: uuid.UUID,
    request_body: UpdatePayeeRequest,
    request: Request,
    db: Session = Depends(get_db)
):
    """Update payee"""
    customer_id, profile_id = get_current_customer_and_profile(request)

    # Check entitlement
    entitlement_service = EntitlementService()
    entitlement_service.require_capability(db, profile_id, "manage_payees")

    # Update payee
    payee_service = PayeeService()
    payee, cop_check = payee_service.update_payee(
        db=db,
        payee_id=payee_id,
        customer_id=customer_id,
        payee_name=request_body.payee_name,
        sort_code=request_body.sort_code,
        account_number=request_body.account_number,
    )

    db.commit()

    cop_check_out = None
    if cop_check:
        cop_check_out = CopCheckOut(
            cop_check_id=cop_check.cop_check_id,
            outcome=cop_check.outcome,
            suggested_name=cop_check.suggested_name,
            policy_treatment=cop_check.policy_treatment,
            checked_at=cop_check.checked_at,
            expires_at=cop_check.expires_at,
            customer_acknowledged_at=cop_check.customer_acknowledged_at,
        )

    return UpdatePayeeResponse(
        payee=payee_to_out(payee),
        cop_check=cop_check_out,
    )


@router.post("/{payee_id}/cop-acknowledgement", response_model=AcknowledgeCopResponse)
def acknowledge_cop(
    payee_id: uuid.UUID,
    request_body: AcknowledgeCopRequest,
    request: Request,
    db: Session = Depends(get_db)
):
    """Acknowledge CoP mismatch/partial match"""
    customer_id, profile_id = get_current_customer_and_profile(request)

    # Check entitlement
    entitlement_service = EntitlementService()
    entitlement_service.require_capability(db, profile_id, "manage_payees")

    # Verify payee belongs to customer
    payee_service = PayeeService()
    payee_service.get_payee_by_id(db, payee_id, customer_id)

    # Record acknowledgement
    cop_service = CopService()
    cop_check = cop_service.acknowledge_cop_result(db, payee_id, customer_id)

    db.commit()

    return AcknowledgeCopResponse(
        payee_id=payee_id,
        acknowledged_at=cop_check.customer_acknowledged_at,
        message="CoP acknowledgement recorded"
    )


@router.post("/{payee_id}/cop-checks", response_model=RunCopCheckResponse)
def run_cop_check(
    payee_id: uuid.UUID,
    request_body: RunCopCheckRequest,
    request: Request,
    db: Session = Depends(get_db)
):
    """Manually run CoP check for payee"""
    customer_id, profile_id = get_current_customer_and_profile(request)

    # Check entitlement
    entitlement_service = EntitlementService()
    entitlement_service.require_capability(db, profile_id, "manage_payees")

    # Get payee
    payee_service = PayeeService()
    payee = payee_service.get_payee_by_id(db, payee_id, customer_id)

    # Decrypt account number
    import base64

    from cryptography.fernet import Fernet

    from app.config import settings
    key_bytes = settings.secret_key.encode()[:32].ljust(32, b'0')
    fernet_key = base64.urlsafe_b64encode(key_bytes)
    fernet = Fernet(fernet_key)
    account_number = fernet.decrypt(payee.account_number_encrypted.encode()).decode()

    # Run CoP check
    cop_service = CopService()
    cop_check = cop_service.run_cop_check(
        db=db,
        payee_id=payee_id,
        payee_name=payee.payee_name,
        sort_code=payee.sort_code,
        account_number=account_number,
        trigger=request_body.reason
    )

    db.commit()

    return RunCopCheckResponse(
        cop_check=CopCheckOut(
            cop_check_id=cop_check.cop_check_id,
            outcome=cop_check.outcome,
            suggested_name=cop_check.suggested_name,
            policy_treatment=cop_check.policy_treatment,
            checked_at=cop_check.checked_at,
            expires_at=cop_check.expires_at,
            customer_acknowledged_at=cop_check.customer_acknowledged_at,
        )
    )

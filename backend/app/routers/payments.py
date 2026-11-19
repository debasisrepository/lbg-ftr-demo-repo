"""Payment domain API endpoints."""
from fastapi import APIRouter, Depends, Request
from sqlalchemy.orm import Session
from app.database import get_db
from app.middleware.auth_context import get_current_user, get_current_session
from app.schemas.payment_schemas import (
    PaymentPrepareRequest,
    PaymentPrepareResponse,
    PaymentApproveRequest,
    PaymentApproveResponse,
    PaymentStatusResponse
)
from app.services.payment_orchestration_service import PaymentOrchestrationService
from app.models.auth import UserIdentity, AuthSession
from app.common.correlation import get_correlation_id


router = APIRouter(prefix="/payments", tags=["payments"])


@router.post("/prepare", response_model=PaymentPrepareResponse)
def prepare_payment(
    request: Request,
    payment_request: PaymentPrepareRequest,
    current_user: UserIdentity = Depends(get_current_user),
    current_session: AuthSession = Depends(get_current_session),
    db: Session = Depends(get_db)
):
    """Prepare a payment with validation and fraud check."""
    correlation_id = get_correlation_id(request)
    service = PaymentOrchestrationService(db, correlation_id)
    
    result = service.prepare_payment(
        profile_id=payment_request.profile_id,
        source_account_id=payment_request.source_account_id,
        payee_id=payment_request.payee_id,
        amount_minor=payment_request.amount_minor,
        currency=payment_request.currency,
        reference=payment_request.reference,
        client_idempotency_key=payment_request.client_idempotency_key,
        auth_session_id=current_session.id,
        user_identity_id=current_user.id
    )
    
    return PaymentPrepareResponse(**result)


@router.post("/{payment_id}/approve", response_model=PaymentApproveResponse)
def approve_payment(
    request: Request,
    payment_id: int,
    approve_request: PaymentApproveRequest,
    current_user: UserIdentity = Depends(get_current_user),
    current_session: AuthSession = Depends(get_current_session),
    db: Session = Depends(get_db)
):
    """Approve payment after SCA verification."""
    correlation_id = get_correlation_id(request)
    service = PaymentOrchestrationService(db, correlation_id)
    
    result = service.approve_payment(
        payment_id=payment_id,
        challenge_id=approve_request.challenge_id,
        method=approve_request.method,
        passcode=approve_request.passcode,
        biometric_assertion=approve_request.biometric_assertion,
        device_id=approve_request.device_id,
        auth_session_id=current_session.id,
        user_identity_id=current_user.id
    )
    
    return PaymentApproveResponse(**result)


@router.get("/{payment_id}", response_model=PaymentStatusResponse)
def get_payment_status(
    request: Request,
    payment_id: int,
    current_user: UserIdentity = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get payment status."""
    correlation_id = get_correlation_id(request)
    service = PaymentOrchestrationService(db, correlation_id)
    
    result = service.get_payment_status(
        payment_id=payment_id,
        user_identity_id=current_user.id
    )
    
    return PaymentStatusResponse(**result)

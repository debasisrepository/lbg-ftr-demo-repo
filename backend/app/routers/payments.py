"""
Payments router - payment initiation and management endpoints.
Requirement: REQ-PAY-002, REQ-PAY-003, REQ-PAY-004, REQ-PAY-005, REQ-PAY-006, REQ-PAY-007
"""
from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, Header, Query, Response
from sqlalchemy.orm import Session

from app.database import get_db
from app.middleware.auth_middleware import get_current_user
from app.middleware.correlation_middleware import get_correlation_id
from app.schemas.auth_schemas import UserSummary
from app.schemas.payments_schemas import (
    PaymentChangeRequest,
    PaymentCreateRequest,
    PaymentListResponse,
    PaymentResponse,
    PaymentSubmitRequest,
    WarningDecisionRequest,
)
from app.services.payment_orchestration_service import PaymentOrchestrationService

router = APIRouter()


@router.post("", response_model=PaymentResponse, status_code=201)
def create_payment_review(
    request: PaymentCreateRequest,
    response: Response,
    idempotency_key: Annotated[str, Header(min_length=8, max_length=64, alias="Idempotency-Key")],
    db: Session = Depends(get_db),
    current_user: UserSummary = Depends(get_current_user),
    correlation_id: str = Depends(get_correlation_id)
):
    """
    E-07: Create payment review.
    
    Creates a PaymentIntent in state draft then review_ready with review_version 1
    and review_fingerprint (SHA-256 over source_account_reference, payee_id,
    amount_minor, currency, payment_reference_text, review_version).
    
    Checks:
    - Source account payment_source_eligible
    - Payee saved_active
    - Payments capability not unavailable
    
    Idempotency: Same key + fingerprint returns stored result with Idempotent-Replayed: true.
    Same key + different fingerprint returns 422 idempotency_key_reuse.
    
    Returns PaymentResponse with current_state review_ready, next_action review_and_approve.
    """
    service = PaymentOrchestrationService(db)
    
    payment_response, is_replay = service.create_payment_review(
        request=request,
        customer_id=current_user.id,  # type: ignore[arg-type]
        idempotency_key=idempotency_key,
        correlation_id=correlation_id
    )
    
    # Set Idempotent-Replayed header if replay
    if is_replay:
        response.headers["Idempotent-Replayed"] = "true"
    
    return payment_response


@router.post("/{payment_id}/warning-decision", response_model=PaymentResponse)
def record_warning_decision(
    payment_id: UUID,
    request: WarningDecisionRequest,
    db: Session = Depends(get_db),
    current_user: UserSummary = Depends(get_current_user),
    correlation_id: str = Depends(get_correlation_id)
):
    """
    E-12: Record warning decision (stop or continue).
    
    Valid only while current_state is warning_presented.
    
    'stop' moves payment to stopped_after_warning; nothing is submitted.
    Response shows current_state stopped_after_warning, is_submitted false.
    
    'continue' accepted only when policy_allows_continue is true.
    Writes scam_check_outcomes with customer_decision='continued',
    writes audit_events row payment.warning_traversed,
    moves to submission_in_progress.
    
    Returns 403 warning_continue_not_permitted if continue requested when not allowed.
    Returns 400 payment_state_invalid if not in warning_presented state.
    Returns 409 review_changed if review_version doesn't match.
    
    Returns PaymentResponse with updated state.
    """
    service = PaymentOrchestrationService(db)
    
    return service.record_warning_decision(
        payment_id=payment_id,
        request=request,
        customer_id=current_user.id,  # type: ignore[arg-type]
        correlation_id=correlation_id
    )


@router.patch("/{payment_id}", response_model=PaymentResponse)
def change_payment_review(
    payment_id: UUID,
    request: PaymentChangeRequest,
    db: Session = Depends(get_db),
    current_user: UserSummary = Depends(get_current_user),
    correlation_id: str = Depends(get_correlation_id)
):
    """
    E-10: Change payment review.
    
    Allowed only in review_ready or awaiting_dynamic_link_approval.
    Changes to critical fields (source account, payee, amount, reference)
    increment review_version and recompute review_fingerprint.
    
    Returns 409 review_not_editable if in later state.
    Returns 409 review_changed if expected_review_version doesn't match.
    
    Returns updated PaymentResponse.
    """
    service = PaymentOrchestrationService(db)
    
    return service.change_payment_review(
        payment_id=payment_id,
        request=request,
        customer_id=current_user.id,  # type: ignore[arg-type]
        correlation_id=correlation_id
    )


@router.get("/{payment_id}", response_model=PaymentResponse)
def get_payment(
    payment_id: UUID,
    db: Session = Depends(get_db),
    current_user: UserSummary = Depends(get_current_user),
    correlation_id: str = Depends(get_correlation_id)
):
    """
    E-08: Get payment by ID.
    
    Returns the one customer-visible status for the payment from the single convergence function.
    The reference is always returned, so the customer can identify the payment.
    
    Returns PaymentResponse.
    """
    service = PaymentOrchestrationService(db)
    
    return service.get_payment(
        payment_id=payment_id,
        customer_id=current_user.id  # type: ignore[arg-type]
    )


@router.get("", response_model=PaymentListResponse)
def list_payments(
    idempotency_key: str | None = Query(None, min_length=8, max_length=64),
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=50),
    db: Session = Depends(get_db),
    current_user: UserSummary = Depends(get_current_user),
    correlation_id: str = Depends(get_correlation_id)
):
    """
    E-09: List payments.
    
    Returns the caller's payments newest first.
    With idempotency_key, returns the payment created/submitted under that key (reconnect).
    
    Returns PaymentListResponse with items, total, page, page_size.
    """
    service = PaymentOrchestrationService(db)
    
    return service.list_payments(
        customer_id=current_user.id,  # type: ignore[arg-type]
        idempotency_key=idempotency_key,
        page=page,
        page_size=page_size
    )


@router.post("/{payment_id}/submit", response_model=PaymentResponse)
def approve_and_submit_payment(
    payment_id: UUID,
    request: PaymentSubmitRequest,
    response: Response,
    idempotency_key: Annotated[str, Header(min_length=8, max_length=64, alias="Idempotency-Key")],
    db: Session = Depends(get_db),
    current_user: UserSummary = Depends(get_current_user),
    correlation_id: str = Depends(get_correlation_id)
):
    """
    E-11: Approve and submit payment (approval step only).
    
    Processing order:
    1. Idempotency check - same key + body returns stored result
    2. CIAM step-up approval bound to review fields and fingerprint
    3. Compare signed approval with canonical intent
    4. Any mismatch rejects execution, leaves payment unexecuted
    5. Successful approval moves to fraud_check_in_progress (actual fraud call in next task)
    6. Failed/abandoned approval returns approval_failed_or_abandoned
    
    Returns PaymentResponse.
    """
    service = PaymentOrchestrationService(db)
    
    payment_response, is_replay = service.approve_and_submit(
        payment_id=payment_id,
        request=request,
        customer_id=current_user.id,  # type: ignore[arg-type]
        idempotency_key=idempotency_key,
        correlation_id=correlation_id
    )
    
    # Set Idempotent-Replayed header if replay
    if is_replay:
        response.headers["Idempotent-Replayed"] = "true"
    
    return payment_response

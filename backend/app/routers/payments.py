"""Payment endpoints"""
import uuid

from fastapi import APIRouter, Depends, HTTPException, Request
from sqlalchemy.orm import Session

from ..core.middleware import get_correlation_id
from ..database import get_db
from ..schemas.payment_schemas import (
    PaymentApprovalRequest,
    PaymentApprovalResponse,
    PaymentDetailResponse,
    PaymentPrepareRequest,
    PaymentPrepareResponse,
    PaymentReceiptResponse,
    PaymentRiskResponseRequest,
    PaymentRiskResponseResponse,
    PaymentSubmitRequest,
    PaymentSubmitResponse,
)
from ..services.fraud_service import FraudService
from ..services.payment_service import PaymentService
from ..services.treatment_mapper import TreatmentMapper

router = APIRouter()


def get_current_customer_id() -> uuid.UUID:
    """Stub: get customer ID from session"""
    return uuid.UUID("10000000-0000-0000-0000-000000000001")


def get_current_profile_id() -> uuid.UUID:
    """Stub: get profile ID from session"""
    return uuid.UUID("10000000-0000-0000-0000-000000000101")


def get_current_device_id() -> uuid.UUID:
    """Stub: get device ID from session"""
    return uuid.UUID("10000000-0000-0000-0000-000000000201")


@router.post("/prepare", response_model=PaymentPrepareResponse, status_code=200)
def prepare_payment(
    request: Request,
    payment_request: PaymentPrepareRequest,
    db: Session = Depends(get_db)
):
    """Prepare a new payment"""
    customer_id = get_current_customer_id()
    profile_id = get_current_profile_id()
    correlation_id = get_correlation_id(request)

    payment_service = PaymentService(db)
    fraud_service = FraudService(db)

    try:
        result = payment_service.prepare_payment(
            customer_id,
            profile_id,
            payment_request.source_account_id,
            payment_request.payee_id,
            payment_request.amount_minor,
            payment_request.currency_code,
            payment_request.payment_reference,
            payment_request.idempotency_key,
            correlation_id
        )

        payment_order = result["payment_order"]
        account_name = result["account_name"]
        payee_name = result["payee_name"]

        # Get risk assessment
        risk_assessment = fraud_service.risk_assessment_repo.get_by_payment_order(payment_order.payment_order_id)

        return PaymentPrepareResponse(
            payment_order_id=payment_order.payment_order_id,
            customer_payment_ref=payment_order.customer_payment_ref,
            payment_reference=payment_order.payment_reference,
            amount_minor=payment_order.amount_minor,
            currency_code=payment_order.currency_code,
            source_account_name=account_name,
            payee_name=payee_name,
            limit_checks_passed=True,  # Simplified
            risk_decision=risk_assessment.decision if risk_assessment else "allow",
            requires_approval=True,
            dynamic_link_digest=payment_order.dynamic_link_digest
        )
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/{payment_order_id}/approve", response_model=PaymentApprovalResponse, status_code=200)
def approve_payment(
    payment_order_id: uuid.UUID,
    approval_request: PaymentApprovalRequest,
    request: Request,
    db: Session = Depends(get_db)
):
    """Approve payment with SCA"""
    customer_id = get_current_customer_id()
    device_id = get_current_device_id()
    correlation_id = get_correlation_id(request)

    payment_service = PaymentService(db)

    try:
        payment_order = payment_service.approve_payment(
            payment_order_id,
            device_id,
            customer_id,
            correlation_id,
            approval_request.step_up_challenge_ref
        )

        return PaymentApprovalResponse(
            payment_order_id=payment_order.payment_order_id,
            approval_result="approved",
            message="Payment approved successfully",
            next_step="submit"
        )
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/{payment_order_id}/risk-response", response_model=PaymentRiskResponseResponse, status_code=200)
def respond_to_risk(
    payment_order_id: uuid.UUID,
    risk_response: PaymentRiskResponseRequest,
    request: Request,
    db: Session = Depends(get_db)
):
    """Respond to risk warning/challenge"""
    get_correlation_id(request)

    fraud_service = FraudService(db)

    try:
        risk_assessment = fraud_service.risk_assessment_repo.get_by_payment_order(payment_order_id)

        if not risk_assessment:
            raise HTTPException(status_code=404, detail="Risk assessment not found")

        if risk_response.acknowledged:
            fraud_service.acknowledge_risk_warning(risk_assessment, risk_response.purpose_answer)

        can_proceed = TreatmentMapper.can_proceed(risk_assessment.decision)

        return PaymentRiskResponseResponse(
            payment_order_id=payment_order_id,
            decision=risk_assessment.decision,
            can_proceed=can_proceed,
            message=TreatmentMapper.get_customer_message(risk_assessment.decision, risk_assessment.treatment_reason_code)
        )
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/{payment_order_id}/submit", response_model=PaymentSubmitResponse, status_code=200)
def submit_payment(
    payment_order_id: uuid.UUID,
    submit_request: PaymentSubmitRequest,
    request: Request,
    db: Session = Depends(get_db)
):
    """Submit payment to hub"""
    customer_id = get_current_customer_id()
    correlation_id = get_correlation_id(request)

    payment_service = PaymentService(db)

    try:
        payment_order = payment_service.submit_payment(
            payment_order_id,
            customer_id,
            correlation_id
        )

        return PaymentSubmitResponse(
            payment_order_id=payment_order.payment_order_id,
            external_payment_ref=payment_order.external_payment_ref,
            normalized_status=payment_order.normalized_status,
            current_internal_state=payment_order.current_internal_state,
            submitted_at=payment_order.submitted_at,
            expected_arrival_text=payment_order.expected_arrival_text
        )
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/{payment_order_id}", response_model=PaymentDetailResponse, status_code=200)
def get_payment(
    payment_order_id: uuid.UUID,
    db: Session = Depends(get_db)
):
    """Get payment details"""
    payment_service = PaymentService(db)

    payment_order = payment_service.get_payment(payment_order_id)

    if not payment_order:
        raise HTTPException(status_code=404, detail="Payment order not found")

    return PaymentDetailResponse(
        payment_order_id=payment_order.payment_order_id,
        customer_payment_ref=payment_order.customer_payment_ref,
        payment_reference=payment_order.payment_reference,
        amount_minor=payment_order.amount_minor,
        currency_code=payment_order.currency_code,
        payment_type=payment_order.payment_type,
        source_account_id=payment_order.source_account_id,
        payee_id=payment_order.payee_id,
        current_internal_state=payment_order.current_internal_state,
        normalized_status=payment_order.normalized_status,
        latest_status_at=payment_order.latest_status_at,
        external_payment_ref=payment_order.external_payment_ref,
        expected_arrival_text=payment_order.expected_arrival_text,
        submitted_at=payment_order.submitted_at,
        completed_at=payment_order.completed_at,
        created_at=payment_order.created_at
    )


@router.get("/{payment_order_id}/receipt", response_model=PaymentReceiptResponse, status_code=200)
def get_payment_receipt(
    payment_order_id: uuid.UUID,
    db: Session = Depends(get_db)
):
    """Get payment receipt"""
    payment_service = PaymentService(db)

    result = payment_service.get_payment_with_details(payment_order_id)

    if not result:
        raise HTTPException(status_code=404, detail="Payment order not found")

    payment_order = result["payment_order"]
    account_name = result["account_name"]
    payee_name = result["payee_name"]

    return PaymentReceiptResponse(
        payment_order_id=payment_order.payment_order_id,
        customer_payment_ref=payment_order.customer_payment_ref,
        payment_reference=payment_order.payment_reference,
        amount_minor=payment_order.amount_minor,
        currency_code=payment_order.currency_code,
        payee_name=payee_name,
        source_account_name=account_name,
        normalized_status=payment_order.normalized_status,
        expected_arrival_text=payment_order.expected_arrival_text,
        submitted_at=payment_order.submitted_at,
        completed_at=payment_order.completed_at
    )

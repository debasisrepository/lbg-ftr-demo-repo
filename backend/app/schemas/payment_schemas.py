"""Payment-related Pydantic schemas"""
import uuid
from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field


class PaymentPrepareRequest(BaseModel):
    """Request to prepare a new payment"""
    source_account_id: uuid.UUID
    payee_id: uuid.UUID
    amount_minor: int = Field(gt=0)
    currency_code: str = Field(default="GBP", max_length=3)
    payment_reference: str | None = Field(default=None, max_length=35)
    idempotency_key: str = Field(max_length=128)


class PaymentPrepareResponse(BaseModel):
    """Response from payment preparation"""
    payment_order_id: uuid.UUID
    customer_payment_ref: str
    payment_reference: str | None
    amount_minor: int
    currency_code: str
    source_account_name: str
    payee_name: str
    limit_checks_passed: bool
    risk_decision: str
    requires_approval: bool
    dynamic_link_digest: str

    model_config = ConfigDict(from_attributes=True)


class PaymentApprovalRequest(BaseModel):
    """Request to approve a payment with SCA"""
    step_up_challenge_ref: str | None = None
    device_attestation: str | None = None


class PaymentApprovalResponse(BaseModel):
    """Response from payment approval"""
    payment_order_id: uuid.UUID
    approval_result: str
    message: str
    next_step: str | None = None

    model_config = ConfigDict(from_attributes=True)


class PaymentRiskResponseRequest(BaseModel):
    """Customer response to risk warning/challenge"""
    acknowledged: bool
    purpose_answer: str | None = Field(default=None, max_length=64)


class PaymentRiskResponseResponse(BaseModel):
    """Response after risk acknowledgment"""
    payment_order_id: uuid.UUID
    decision: str
    can_proceed: bool
    message: str

    model_config = ConfigDict(from_attributes=True)


class PaymentSubmitRequest(BaseModel):
    """Request to submit payment to hub"""
    pass  # Empty body, operation is idempotent


class PaymentSubmitResponse(BaseModel):
    """Response from payment submission"""
    payment_order_id: uuid.UUID
    external_payment_ref: str | None
    normalized_status: str
    current_internal_state: str
    submitted_at: datetime | None
    expected_arrival_text: str | None

    model_config = ConfigDict(from_attributes=True)


class PaymentDetailResponse(BaseModel):
    """Detailed payment order information"""
    payment_order_id: uuid.UUID
    customer_payment_ref: str
    payment_reference: str | None
    amount_minor: int
    currency_code: str
    payment_type: str
    source_account_id: uuid.UUID
    source_account_name: str
    payee_id: uuid.UUID
    payee_name: str
    current_internal_state: str
    normalized_status: str
    latest_status_at: datetime
    external_payment_ref: str | None
    expected_arrival_text: str | None
    submitted_at: datetime | None
    completed_at: datetime | None
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


class PaymentReceiptResponse(BaseModel):
    """Payment receipt for customer"""
    payment_order_id: uuid.UUID
    customer_payment_ref: str
    payment_reference: str | None
    amount_minor: int
    currency_code: str
    payee_name: str
    source_account_name: str
    normalized_status: str
    expected_arrival_text: str | None
    submitted_at: datetime | None
    completed_at: datetime | None

    model_config = ConfigDict(from_attributes=True)

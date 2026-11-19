"""Payment domain request and response schemas."""
from datetime import datetime
from pydantic import BaseModel, Field


# Shared nested schemas
class PayeeInfo(BaseModel):
    """Payee information in payment responses."""
    payee_id: int
    display_name: str
    sort_code: str | None = None
    masked_account_number: str | None = None


class BalanceCheck(BaseModel):
    """Balance validation result."""
    passed: bool
    available_balance_minor: int
    detail: str | None = None


class LimitCheck(BaseModel):
    """Payment limit validation result."""
    passed: bool
    configured_limit_minor: int
    detail: str | None = None


class FraudDecisionResponse(BaseModel):
    """Fraud decision outcome."""
    decision: str  # allow, warn, step_up, hold
    warning_message: str | None = None
    hold_reason: str | None = None


class DynamicLinkSummary(BaseModel):
    """Dynamic link approval context."""
    payee_name: str
    amount_minor: int
    currency: str


class ApprovalChallenge(BaseModel):
    """SCA approval challenge details."""
    challenge_id: int
    challenge_expires_at: datetime
    dynamic_link_summary: DynamicLinkSummary


# Prepare payment request/response
class PaymentPrepareRequest(BaseModel):
    """Request to prepare a payment."""
    profile_id: int
    source_account_id: int
    payee_id: int
    amount_minor: int = Field(gt=0)
    currency: str = Field(default="GBP", max_length=3)
    reference: str | None = Field(default=None, max_length=255)
    client_idempotency_key: str | None = None


class PaymentPrepareResponse(BaseModel):
    """Response from payment preparation."""
    payment_id: int
    payment_state: str
    amount_minor: int
    currency: str
    source_account_id: int
    payee: PayeeInfo
    reference: str | None
    balance_check: BalanceCheck
    limit_check: LimitCheck
    fraud_decision: FraudDecisionResponse
    approval_required: bool
    approval_challenge: ApprovalChallenge | None = None


# Approve payment request/response
class PaymentApproveRequest(BaseModel):
    """Request to approve a payment."""
    challenge_id: int
    method: str  # passcode, biometric, dynamic_link
    passcode: str | None = None
    biometric_assertion: str | None = None
    device_id: str | None = None


class PaymentApproveResponse(BaseModel):
    """Response from payment approval."""
    payment_id: int
    status: str  # sent, pending, failed
    amount_minor: int
    currency: str
    payee: PayeeInfo
    reference: str | None
    payment_reference: str | None
    rail_reference: str | None = None
    expected_arrival_message: str | None = None
    duplicate_submission_blocked: bool
    next_actions: list[str]


# Get payment status response
class PaymentStatusResponse(BaseModel):
    """Payment status response."""
    payment_id: int
    status: str  # sent, pending, failed
    amount_minor: int
    currency: str
    payee: PayeeInfo
    reference: str | None
    payment_reference: str | None
    rail_reference: str | None = None
    expected_arrival_message: str | None = None
    duplicate_submission_blocked: bool
    status_last_updated_at: datetime
    failure_reason: str | None = None

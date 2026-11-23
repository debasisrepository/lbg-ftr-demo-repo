"""
Payment domain schemas for requests and responses.
Requirement: REQ-PAY-002, REQ-PAY-003, REQ-PAY-006, REQ-PAY-007, REQ-PAY-010, REQ-PAY-011
"""
from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field


class PaymentCreateRequest(BaseModel):
    """Request schema for creating a payment review (E-07)."""
    source_account_id: UUID = Field(..., description="Account with payment_source_eligible true")
    payee_id: UUID = Field(..., description="Saved_active payee of the caller")
    amount_minor: int = Field(..., ge=1, description="Amount in minor units (pence)")
    currency: str = Field(default="GBP", pattern="^GBP$", description="ISO 4217 currency code")
    payment_reference: str = Field(..., min_length=1, max_length=18, description="Customer payment reference")


class PaymentAccountSummary(BaseModel):
    """Account summary in payment response."""
    account_id: UUID
    display_name: str
    masked_account_identifier: str

    model_config = ConfigDict(from_attributes=True)


class PaymentPayeeSummary(BaseModel):
    """Payee summary in payment response."""
    payee_id: UUID
    payee_name: str
    masked_account_identifier: str

    model_config = ConfigDict(from_attributes=True)


class PaymentWarning(BaseModel):
    """Warning details for payment response (E-11, E-12)."""
    heading: str = Field(..., description="Warning heading")
    body: str = Field(..., description="Plain-language warning text")
    allowed_actions: list[str] = Field(..., description="Governed next steps: stop and/or continue")
    policy_allows_continue: bool = Field(..., description="Whether policy allows continue")

    model_config = ConfigDict(from_attributes=True)


class PaymentResponse(BaseModel):
    """
    Unified payment response for E-07, E-08, E-09, E-10, E-11, E-12.
    Covers create review, get payment, change review, warning decision endpoints.
    
    Outcome details (REQ-PAY-010, REQ-PAY-011):
    - payment_reference_text: always shown
    - expected_arrival_time: populated only when payments hub supplies it (never estimated)
    - payee_display_name: payee name from payee summary
    """
    payment_id: UUID
    current_state: str = Field(..., description="Internal state machine state")
    next_action: str = Field(..., description="What the app offers next")
    customer_visible_status: str | None = Field(None, description="Sent, Pending, Failed, or null")
    status_message: str = Field(..., description="Plain-language status message")
    is_submitted: bool = Field(..., description="False for draft, review_ready, etc.")
    do_not_resubmit: bool = Field(..., description="True when customer_visible_status is Pending")
    payment_reference: str = Field(..., description="Customer payment reference")
    amount_minor: int = Field(..., description="Amount in minor units")
    currency: str = Field(..., description="ISO 4217 currency code")
    source_account: PaymentAccountSummary
    payee: PaymentPayeeSummary
    review_version: int = Field(..., description="Current review version")
    review_fingerprint: str = Field(..., description="SHA-256 hex over review fields plus version")
    warning: PaymentWarning | None = Field(None, description="Present only when current_state is warning_presented")
    hold_latest_decision_at: datetime | None = Field(None, description="Latest decision date for held payment")
    expected_arrival_time: datetime | None = Field(
        None, 
        description="Expected arrival time from payments hub (never estimated or guessed)"
    )
    payee_display_name: str = Field(description="Payee display name for outcome details")
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


class PaymentChangeRequest(BaseModel):
    """Request schema for changing payment review (E-10)."""
    expected_review_version: int = Field(..., ge=1, description="Review version the customer was looking at")
    source_account_id: UUID | None = Field(None, description="New source account")
    payee_id: UUID | None = Field(None, description="New payee")
    amount_minor: int | None = Field(None, ge=1, description="New amount in minor units")
    payment_reference: str | None = Field(None, min_length=1, max_length=18, description="New reference")


class ApprovalCredential(BaseModel):
    """Step-up credential for dynamic-linking approval (E-11)."""
    method: str = Field(default="passcode", pattern="^passcode$", description="Step-up method")
    passcode: str = Field(..., min_length=4, max_length=12, description="Passcode for step-up")


class PaymentSubmitRequest(BaseModel):
    """Request schema for approving and submitting payment (E-11)."""
    review_version: int = Field(..., ge=1, description="Review version approved")
    review_fingerprint: str = Field(..., min_length=64, max_length=64, description="Fingerprint of approved review")
    approval: ApprovalCredential = Field(..., description="Step-up credential")


class WarningDecisionRequest(BaseModel):
    """Request schema for recording warning decision (E-12)."""
    review_version: int = Field(..., ge=1, description="Review version the warning applies to")
    decision: str = Field(..., pattern="^(stop|continue)$", description="Customer decision: stop or continue")


class PaymentListResponse(BaseModel):
    """List response for E-09."""
    items: list[PaymentResponse] = Field(..., description="Payments on this page")
    total: int = Field(..., description="Total matching payments")
    page: int = Field(..., description="Current page")
    page_size: int = Field(..., description="Page size used")

"""Tool definitions and argument models."""
from typing import Literal
from pydantic import BaseModel, Field
from datetime import datetime


class GetTransactionsArgs(BaseModel):
    arrangement_reference: str = Field(..., max_length=80)
    from_date: datetime
    to_date: datetime
    max_items: int = Field(default=20, ge=1, le=50)


class RequestDocumentArgs(BaseModel):
    evidence_type: str = Field(..., max_length=40)
    display_label: str = Field(..., max_length=120)
    reason_text: str = Field(..., max_length=500)


class ScheduleCallbackArgs(BaseModel):
    preferred_window_text: str = Field(..., max_length=120)
    case_ref: str = Field(..., max_length=20)


class CardControlsArgs(BaseModel):
    card_token: str = Field(..., max_length=80)
    control_action: Literal["freeze", "unfreeze"]
    sca_reference: str = Field(..., max_length=80)


class RetryPaymentArgs(BaseModel):
    payment_ref: str = Field(..., max_length=80)
    sca_reference: str = Field(..., max_length=80)


class CreateCaseArgs(BaseModel):
    problem_statement: str = Field(..., min_length=1, max_length=4000)
    classification_code: str | None = None
    classification_confidence_pct: int | None = Field(default=None, ge=0, le=100)
    route_reason_code: str = Field(..., max_length=40)
    route_reason_text: str = Field(..., max_length=500)


class UpdateCaseArgs(BaseModel):
    case_id: str  # uuid as string
    status_code: str | None = Field(default=None, max_length=40)
    continuation_path: str | None = Field(default=None, max_length=40)


class RouteToQueueArgs(BaseModel):
    case_ref: str = Field(..., max_length=20)
    route_reason_code: str = Field(..., max_length=40)
    urgency: Literal["standard", "high"]
    vulnerability_flag: bool
    regulatory_clock_type: Literal["complaint", "fraud"] | None = None
    summary_text: str = Field(..., max_length=1500)


class TransactionItem(BaseModel):
    transaction_ref: str
    transaction_date: datetime
    amount: float
    merchant_name: str
    status: str


class DocumentRequestResult(BaseModel):
    document_request_ref: str


class CallbackScheduleResult(BaseModel):
    preference_ref: str


class CardControlResult(BaseModel):
    card_state: str
    effective_at: datetime


class PaymentRetryResult(BaseModel):
    payment_status: str
    submitted_at: datetime


class CaseCreationResult(BaseModel):
    case_id: str  # uuid as string
    case_ref: str


class CaseUpdateResult(BaseModel):
    case_id: str  # uuid as string
    status_code: str


class RoutingResult(BaseModel):
    queue_ref: str
    team_display: str
    expected_by_at: datetime

"""Case schemas."""
from datetime import datetime
from typing import Generic, Literal, TypeVar
from uuid import UUID

from pydantic import BaseModel, Field, field_validator

from app.core.restricted_data import RestrictedDataScreen


T = TypeVar("T")


class Page(BaseModel, Generic[T]):
    """Pagination wrapper for list responses."""
    items: list[T]
    total: int
    limit: int
    offset: int


class CaseCreateRequest(BaseModel):
    """Request to create a new case."""
    issue_type: str = Field(..., min_length=1, max_length=60)
    issue_summary: str = Field(..., min_length=1, max_length=2000)
    issue_title: str | None = Field(None, min_length=1, max_length=160)
    origin_channel: Literal["mobile_app", "web", "chat", "phone", "branch", "colleague_desktop"] = Field(...)
    brand: Literal["lloyds", "bank_of_scotland"] | None = None
    customer_party_id: str | None = Field(None, min_length=1, max_length=64)
    existing_case_reference: str | None = Field(None, min_length=1, max_length=32)

    @field_validator("issue_summary", "issue_title")
    @classmethod
    def check_restricted_data(cls, v: str | None) -> str | None:
        """Ensure no restricted data in free text fields."""
        if v and RestrictedDataScreen.contains_restricted(v):
            raise ValueError("Field contains restricted data (PAN, passcode, or security answer)")
        return v


class OwnerView(BaseModel):
    """Owner information view."""
    owner_type: Literal["named_person", "team", "role"] = "team"
    owner_semantic_label: str
    owner_team_code: str | None = None
    owner_display_name: str
    effective_from: datetime


class ExpectedByView(BaseModel):
    """Expected-by commitment view."""
    commitment_state: Literal["committed", "revised", "withdrawn", "under_review"]
    expected_by_at: datetime | None = None
    customer_explanatory_text: str | None = None
    confidence_basis: str | None = None
    effective_from: datetime | None = None


class OwnerChangeRequest(BaseModel):
    """Request to change case owner."""
    owner_team_code: str = Field(..., min_length=1, max_length=100)
    handoff_reason_code: str = Field(..., min_length=1, max_length=100)


class ExpectedByRevisionRequest(BaseModel):
    """Request to revise expected-by commitment."""
    commitment_state: Literal["committed", "revised", "withdrawn", "under_review"] = Field(...)
    expected_by_at: datetime | None = None
    customer_explanatory_text: str | None = Field(None, min_length=1, max_length=1000)
    confidence_basis: str | None = Field(None, min_length=1, max_length=100)
    withdrawn_reason_code: str | None = Field(None, min_length=1, max_length=100)

    @field_validator("customer_explanatory_text")
    @classmethod
    def check_restricted_data(cls, v: str | None) -> str | None:
        """Ensure no restricted data in free text fields."""
        if v and RestrictedDataScreen.contains_restricted(v):
            raise ValueError("Field contains restricted data (PAN, passcode, or security answer)")
        return v


class CaseSummary(BaseModel):
    """Case summary for list views."""
    case_reference: str
    issue_type: str
    issue_title: str | None
    current_lifecycle_state: str
    status_code: str
    status_label: str
    latest_meaningful_update_text: str | None
    latest_meaningful_update_at: datetime | None
    owner: OwnerView
    expected_by: ExpectedByView
    opened_at: datetime
    closed_at: datetime | None
    outcome_summary: str | None


class CaseDetail(BaseModel):
    """Full case detail."""
    case_reference: str
    customer_party_id: str
    brand: Literal["lloyds", "bank_of_scotland"]
    issue_type: str
    classification_source: Literal["eligibility_rule", "intake_agent_recommendation", "colleague"]
    issue_title: str | None
    issue_summary: str | None
    origin_channel: str
    current_lifecycle_state: str
    status_code: str
    status_label: str
    status_summary_text: str | None = None
    latest_meaningful_update_text: str | None
    latest_meaningful_update_at: datetime | None
    next_step_text: str | None
    outage_impact_banner_text: str | None
    owner: OwnerView
    expected_by: ExpectedByView
    opened_at: datetime
    closed_at: datetime | None
    outcome_summary: str | None
    continuity_state: Literal["none", "package_current", "refresh_pending"]


class CaseCreationResult(BaseModel):
    """Response to case creation request."""
    outcome: Literal["created", "surfaced", "not_eligible"]
    case: CaseDetail | None = None
    classification_source: Literal["eligibility_rule", "intake_agent_recommendation", "colleague"] | None = None
    anchor_reference: str | None = None
    redirect_journey_code: str | None = None
    redirect_message: str | None = None
    continuity_available: bool = False


class CaseTransitionRequest(BaseModel):
    """Request to transition a case to a new lifecycle state."""
    to_state: str = Field(..., min_length=1, max_length=50)
    basis_type: Literal["operational_event", "approved_manual_update"] = Field(...)
    basis_reference: str = Field(..., min_length=1, max_length=120)
    status_code: str = Field(..., min_length=1, max_length=60)
    status_label: str = Field(..., min_length=1, max_length=160)
    status_summary_text: str = Field(..., min_length=1, max_length=1000)
    latest_meaningful_update_text: str | None = Field(None, min_length=1, max_length=1000)
    next_step_text: str | None = Field(None, min_length=1, max_length=1000)
    outcome_summary: str | None = Field(None, min_length=1, max_length=2000)

    @field_validator("status_summary_text", "latest_meaningful_update_text", "next_step_text", "outcome_summary")
    @classmethod
    def check_restricted_data(cls, v: str | None) -> str | None:
        """Ensure no restricted data in free text fields."""
        if v and RestrictedDataScreen.contains_restricted(v):
            raise ValueError("Field contains restricted data (PAN, passcode, or security answer)")
        return v


class HistoryEvent(BaseModel):
    """Case history event."""
    id: UUID
    sequence_number: int
    event_type: str
    event_timestamp: datetime
    summary_text: str | None
    customer_visible_flag: bool
    actor_type: str | None
    actor_reference: str | None
    basis_type: str | None
    basis_reference: str | None
    lifecycle_from: str | None = None
    lifecycle_to: str | None = None


class CaseTransitionResult(BaseModel):
    """Response to case transition request."""
    case: CaseDetail
    event: HistoryEvent

"""Colleague API schemas."""
from pydantic import BaseModel, Field
from datetime import datetime


class CreateColleagueCaseRequest(BaseModel):
    """Request to create Case from colleague desktop (H14)."""
    origin_source: str = Field(default="colleague_desktop", max_length=40)
    problem_statement: str = Field(..., min_length=1, max_length=4000)


class ColleagueCaseListItem(BaseModel):
    """Colleague worklist item."""
    case_id: str
    case_ref: str
    status_code: str
    classification_code: str
    owner_team_display: str
    owner_colleague_display: str | None
    expected_by_at: datetime
    last_update_at: datetime


class ColleagueCaseListResponse(BaseModel):
    """Paginated colleague worklist."""
    items: list[ColleagueCaseListItem]
    total: int


class HandoffPackResponse(BaseModel):
    """Hand-off pack for colleague view (H16)."""
    case_id: str
    case_ref: str
    status_code: str
    problem_statement: str
    classification_code: str
    route_reason: str
    arrival_source: str
    expected_by_at: datetime
    owner_team_display: str
    owner_colleague_display: str | None
    handoff_summary_text: str
    vulnerability_flag: bool
    entry_count: int
    evidence_count: int
    copilot_note: str | None


class TranscriptEntryResponse(BaseModel):
    """Transcript entry."""
    entry_id: str
    role: str  # 'customer', 'assistant', 'colleague', 'system'
    content_text: str
    visibility_scope: str  # 'customer_and_colleague' or 'colleague_only'
    occurred_at: datetime


class ThreadResponse(BaseModel):
    """Paginated transcript."""
    entries: list[TranscriptEntryResponse]
    total: int


class ColleagueReplyRequest(BaseModel):
    """Colleague reply to customer (H18)."""
    content_text: str = Field(..., min_length=1, max_length=4000)
    visibility_scope: str = Field(default="customer_and_colleague")  # or 'colleague_only'


class EvidenceRequestRequest(BaseModel):
    """Request additional evidence (H19)."""
    display_label: str = Field(..., max_length=120)
    evidence_type: str = Field(default="document", max_length=40)


class PickupRequest(BaseModel):
    """Pickup case assignment (H21)."""
    colleague_user_id: str  # UUID as string

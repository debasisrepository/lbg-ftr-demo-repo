from pydantic import BaseModel, Field
from datetime import datetime
from uuid import UUID


class StartResolveRequest(BaseModel):
    message_text: str = Field(..., min_length=1, max_length=4000)
    entry_context_type: str | None = None
    entry_context_ref: str | None = None
    status_context_shown: bool = False


class SendMessageRequest(BaseModel):
    message_text: str = Field(..., min_length=1, max_length=4000)


class ResolveTurnEntry(BaseModel):
    role: str
    content_text: str
    occurred_at: datetime


class ResolveTurnResponse(BaseModel):
    session_id: UUID
    thread_id: UUID
    state: str
    ai_disclosure: bool
    human_path_shown: bool
    new_entries: list[ResolveTurnEntry]
    case_ref: str | None = None
    case_id: UUID | None = None
    classification: str | None = None


class ResolveSessionView(BaseModel):
    session_id: UUID
    thread_id: UUID
    state: str
    entries: list[ResolveTurnEntry]
    case_ref: str | None = None
    classification: str | None = None


class HumanRequestResponse(BaseModel):
    session_id: UUID
    thread_id: UUID
    case_ref: str
    case_id: UUID
    owner_team_display: str | None
    expected_by_at: datetime | None


class CreateCaseRequest(BaseModel):
    origin_source: str
    problem_statement: str = Field(..., min_length=1, max_length=10000)


class CaseResponse(BaseModel):
    id: UUID
    case_ref: str
    customer_user_id: int
    status: str
    problem_statement: str
    classification: str | None
    owner_team_display: str | None
    expected_by_at: datetime | None
    created_at: datetime


class CaseListItem(BaseModel):
    id: UUID
    case_ref: str
    status: str
    classification: str | None
    owner_team_display: str | None
    last_update_at: datetime
    expected_by_at: datetime | None


class CaseListResponse(BaseModel):
    items: list[CaseListItem]
    total: int


class CaseDetailResponse(BaseModel):
    id: UUID
    case_ref: str
    customer_user_id: int
    status: str
    problem_statement: str
    classification: str | None
    owner_team_display: str | None
    owner_colleague_display: str | None
    route_reason: str | None
    expected_by_at: datetime | None
    last_update_at: datetime
    created_at: datetime

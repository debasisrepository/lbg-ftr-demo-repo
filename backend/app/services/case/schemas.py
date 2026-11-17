from pydantic import BaseModel, Field
from datetime import datetime
from uuid import UUID


class CreateCaseRequest(BaseModel):
    origin_source: str
    problem_statement: str = Field(..., min_length=1, max_length=10000)
    classification: str | None = None
    arrangement_reference: str | None = None
    route_reason: str | None = None


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

from pydantic import BaseModel, Field, field_validator
from typing import Any
from datetime import datetime
from uuid import UUID


class StartSessionRequest(BaseModel):
    message_text: str = Field(..., min_length=1, max_length=4000)
    entry_context_type: str | None = None
    entry_context_ref: str | None = None
    status_context_shown: bool = False

    @field_validator("entry_context_type")
    @classmethod
    def validate_context_type(cls, v: str | None) -> str | None:
        if v and v not in {"transaction", "issue", "card", "none"}:
            raise ValueError("entry_context_type must be transaction, issue, card, or none")
        return v


class SendMessageRequest(BaseModel):
    message_text: str = Field(..., min_length=1, max_length=4000)


class ResolveTurnEntry(BaseModel):
    role: str
    content_text: str
    occurred_at: datetime


class ResolveTurn(BaseModel):
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

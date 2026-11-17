from datetime import datetime
from pydantic import BaseModel, ConfigDict
import uuid


class AuditLogEntryCreate(BaseModel):
    chain_key: str
    actor_type: str
    source_component: str
    event_class: str
    severity: str = "info"
    entity_type: str
    entity_id: str
    outcome_code: str
    summary_text: str
    correlation_id: str
    retention_class: str = "regulatory"
    case_id: uuid.UUID | None = None
    session_id: uuid.UUID | None = None
    actor_user_id: int | None = None
    actor_agent_code: str | None = None


class AuditLogEntryView(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    chain_key: str
    chain_seq: int
    actor_type: str
    case_id: uuid.UUID | None
    session_id: uuid.UUID | None
    actor_user_id: int | None
    actor_agent_code: str | None
    source_component: str
    event_class: str
    severity: str
    entity_type: str
    entity_id: str
    outcome_code: str
    summary_text: str
    correlation_id: str
    retention_class: str
    previous_entry_hash: str | None
    entry_hash: str
    occurred_at: datetime

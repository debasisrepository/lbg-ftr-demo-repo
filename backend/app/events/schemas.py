from datetime import datetime
from pydantic import BaseModel, ConfigDict
import uuid


class DomainEventCreate(BaseModel):
    event_type: str
    idempotency_key: str
    entity_type: str
    entity_id: str
    payload: dict | None
    correlation_id: str


class DomainEventView(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    event_type: str
    idempotency_key: str
    entity_type: str
    entity_id: str
    payload: dict | None
    correlation_id: str
    occurred_at: datetime


class EventOutboxView(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    event_id: uuid.UUID
    status: str
    retry_count: int
    next_attempt_at: datetime
    published_at: datetime | None
    last_error: str | None

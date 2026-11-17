from datetime import datetime
from sqlalchemy import String, Integer, DateTime, Uuid, Text, Boolean, CheckConstraint, Index, ForeignKey, JSON
from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy.sql import func
import uuid
from app.database import Base
from app.core.clock import Clock


class DomainEvent(Base):
    __tablename__ = "domain_event"

    id: Mapped[uuid.UUID] = mapped_column(Uuid, primary_key=True)
    event_type: Mapped[str] = mapped_column(String(40), nullable=False)
    idempotency_key: Mapped[str] = mapped_column(String(100), nullable=False, unique=True)
    entity_type: Mapped[str] = mapped_column(String(40), nullable=False)
    entity_id: Mapped[str] = mapped_column(String(64), nullable=False)
    payload: Mapped[dict | None] = mapped_column(JSON, nullable=True)
    correlation_id: Mapped[str] = mapped_column(String(64), nullable=False)
    occurred_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, default=Clock.utc_now, server_default=func.current_timestamp())

    __table_args__ = (
        CheckConstraint("event_type IN ('CaseCaptured', 'CaseStatusChanged', 'EvidenceRequested', 'EvidenceReceived', 'DecisionRecorded')", name="ck_domain_event_type"),
        Index("uq_domain_event_idempotency", "idempotency_key", unique=True),
        Index("ix_domain_event_entity", "entity_type", "entity_id"),
    )


class EventOutbox(Base):
    __tablename__ = "event_outbox"

    id: Mapped[uuid.UUID] = mapped_column(Uuid, primary_key=True)
    event_id: Mapped[uuid.UUID] = mapped_column(Uuid, ForeignKey("domain_event.id"), nullable=False, unique=True)
    status: Mapped[str] = mapped_column(String(20), nullable=False)
    retry_count: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    next_attempt_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    published_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    last_error: Mapped[str | None] = mapped_column(Text, nullable=True)

    __table_args__ = (
        CheckConstraint("status IN ('pending', 'published', 'failed')", name="ck_event_outbox_status"),
        Index("ix_event_outbox_status_next_attempt", "status", "next_attempt_at"),
    )

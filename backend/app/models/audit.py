"""Audit and event models."""
import uuid
from datetime import datetime

from sqlalchemy import (
    CheckConstraint,
    DateTime,
    Index,
    Integer,
    String,
    Text,
    UniqueConstraint,
    Uuid,
)
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy.types import JSON

from app.database import Base


class AuditEntry(Base):
    """Immutable audit entry (append-only)."""

    __tablename__ = "audit_entries"

    id: Mapped[uuid.UUID] = mapped_column(Uuid, primary_key=True, default=uuid.uuid4)
    correlation_id: Mapped[str] = mapped_column(String(255), nullable=False, index=True)
    audit_category: Mapped[str] = mapped_column(String(50), nullable=False, index=True)
    event_type: Mapped[str] = mapped_column(String(100), nullable=False)
    actor_type: Mapped[str | None] = mapped_column(String(50), nullable=True)
    actor_reference: Mapped[str | None] = mapped_column(String(255), nullable=True, index=True)
    entity_type: Mapped[str | None] = mapped_column(String(100), nullable=True)
    entity_id: Mapped[str | None] = mapped_column(String(255), nullable=True, index=True)
    state_before_hash: Mapped[str | None] = mapped_column(String(255), nullable=True)
    state_after_hash: Mapped[str | None] = mapped_column(String(255), nullable=True)
    severity: Mapped[str] = mapped_column(String(20), nullable=False, default="info")
    metadata_json: Mapped[dict | None] = mapped_column(JSON().with_variant(JSONB(), "postgresql"), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, index=True)

    __table_args__ = (
        CheckConstraint(
            "audit_category IN ('case_change', 'access', 'policy', 'action', 'communication', 'fallback_exposure', 'system')",
            name="ck_audit_category",
        ),
        CheckConstraint(
            "severity IN ('debug', 'info', 'warning', 'error', 'critical')",
            name="ck_severity",
        ),
        Index("ix_audit_category_created", audit_category, created_at),
    )


class CaseEvent(Base):
    """Case event store (append-only)."""

    __tablename__ = "case_events"

    id: Mapped[uuid.UUID] = mapped_column(Uuid, primary_key=True, default=uuid.uuid4)
    case_id: Mapped[uuid.UUID] = mapped_column(Uuid, nullable=False, index=True)
    sequence_number: Mapped[int] = mapped_column(Integer, nullable=False)
    event_type: Mapped[str] = mapped_column(String(100), nullable=False)
    event_timestamp: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    summary_text: Mapped[str | None] = mapped_column(Text, nullable=True)
    event_payload_json: Mapped[dict | None] = mapped_column(JSON().with_variant(JSONB(), "postgresql"), nullable=True)
    customer_visible_flag: Mapped[bool] = mapped_column(default=True, nullable=False)
    actor_type: Mapped[str | None] = mapped_column(String(50), nullable=True)
    actor_reference: Mapped[str | None] = mapped_column(String(255), nullable=True)
    basis_type: Mapped[str | None] = mapped_column(String(50), nullable=True)
    basis_reference: Mapped[str | None] = mapped_column(String(255), nullable=True)
    correlation_id: Mapped[str | None] = mapped_column(String(255), nullable=True, index=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)

    __table_args__ = (
        UniqueConstraint("case_id", "sequence_number", name="uq_case_event_sequence"),
        Index("ix_case_event_case_sequence", case_id, sequence_number),
    )

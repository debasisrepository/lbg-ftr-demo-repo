"""Audit event models."""
import uuid
from datetime import datetime

from sqlalchemy import JSON, CheckConstraint, DateTime, ForeignKey, Index, String, Uuid
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column

from app.core.db import Base


class AuditEvent(Base):
    """Audit event record."""

    __tablename__ = "audit_events"

    id: Mapped[uuid.UUID] = mapped_column(Uuid, primary_key=True, default=uuid.uuid4)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)

    event_type: Mapped[str] = mapped_column(String(50), nullable=False, index=True)
    severity: Mapped[str] = mapped_column(String(50), nullable=False, default="info")
    actor_user_id: Mapped[uuid.UUID | None] = mapped_column(Uuid, ForeignKey("users.id"), nullable=True, index=True)
    actor_role_code: Mapped[str | None] = mapped_column(String(50), nullable=True)
    customer_account_id: Mapped[uuid.UUID | None] = mapped_column(Uuid, ForeignKey("customer_accounts.id"), nullable=True, index=True)
    affected_entity_type: Mapped[str | None] = mapped_column(String(50), nullable=True, index=True)
    affected_entity_id: Mapped[uuid.UUID | None] = mapped_column(Uuid, nullable=True)
    correlation_id: Mapped[str] = mapped_column(String(36), nullable=False, index=True)
    event_timestamp: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, index=True)
    rationale_text: Mapped[str | None] = mapped_column(String(1000), nullable=True)
    policy_evaluation_record_id: Mapped[uuid.UUID | None] = mapped_column(
        Uuid, ForeignKey("policy_evaluation_records.id"), nullable=True, index=True
    )
    event_payload_json: Mapped[dict] = mapped_column(
        JSON().with_variant(JSONB(), "postgresql"), nullable=False, default=dict
    )

    __table_args__ = (
        CheckConstraint(
            "event_type IN ('login_success', 'login_failure', 'logout', 'session_expired', "
            "'role_switched', 'authorization_denied', 'queue_refreshed', 'policy_evaluated', "
            "'promise_created', 'promise_rejected', 'sap_adapter_failure')",
            name="ck_audit_events_type"
        ),
        CheckConstraint("severity IN ('debug', 'info', 'warning', 'error', 'critical')", name="ck_audit_events_severity"),
        Index("ix_audit_events_entity", "affected_entity_type", "affected_entity_id"),
        Index("ix_audit_events_account_time", "customer_account_id", "event_timestamp"),
    )

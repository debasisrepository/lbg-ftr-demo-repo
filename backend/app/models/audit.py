"""Audit event model"""
import uuid
from datetime import UTC, datetime

from sqlalchemy import JSON as SQLiteJSON
from sqlalchemy import CheckConstraint, DateTime, ForeignKey, Index, String, Uuid
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column

from ..database import Base

# JSON type that works with both PostgreSQL and SQLite
JSON = JSONB().with_variant(SQLiteJSON(), "sqlite")


class AuditEvent(Base):
    """Audit trail (FR-001 through FR-009, NFR-007, NFR-033 through NFR-036, NFR-046) - append-only"""
    __tablename__ = "audit_event"

    audit_event_id: Mapped[uuid.UUID] = mapped_column(Uuid, primary_key=True, default=uuid.uuid4)
    customer_id: Mapped[uuid.UUID | None] = mapped_column(Uuid, ForeignKey("customer.customer_id"), nullable=True)
    payment_order_id: Mapped[uuid.UUID | None] = mapped_column(Uuid, ForeignKey("payment_order.payment_order_id"), nullable=True)
    actor_type: Mapped[str] = mapped_column(String(16), nullable=False)
    actor_id: Mapped[str] = mapped_column(String(128), nullable=False)
    event_type: Mapped[str] = mapped_column(String(64), nullable=False)
    event_category: Mapped[str] = mapped_column(String(24), nullable=False)
    entity_type: Mapped[str | None] = mapped_column(String(48), nullable=True)
    entity_id: Mapped[str | None] = mapped_column(String(128), nullable=True)
    outcome: Mapped[str] = mapped_column(String(16), nullable=False)
    severity: Mapped[str] = mapped_column(String(12), nullable=False, default='info')
    customer_ref: Mapped[str | None] = mapped_column(String(128), nullable=True)
    payment_ref: Mapped[str | None] = mapped_column(String(32), nullable=True)
    correlation_id: Mapped[str] = mapped_column(String(128), nullable=False)
    detail_json: Mapped[dict[str, object] | None] = mapped_column(JSON, nullable=True)
    occurred_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    retain_until: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, default=lambda: datetime.now(UTC))

    __table_args__ = (
        CheckConstraint("actor_type IN ('customer', 'system', 'service', 'operator')", name='ck_audit_actor'),
        CheckConstraint(
            "event_category IN ('authentication', 'entitlement', 'payee', 'payment', 'fraud', 'notification', 'operational')",
            name='ck_audit_category'
        ),
        CheckConstraint("outcome IN ('success', 'failure', 'denied', 'held', 'info')", name='ck_audit_outcome'),
        CheckConstraint("severity IN ('info', 'warning', 'error', 'critical')", name='ck_audit_severity'),
        CheckConstraint("retain_until > occurred_at", name='ck_audit_retention'),
        Index('idx_audit_customer_time', 'customer_id', 'occurred_at'),
        Index('idx_audit_customer_ref_time', 'customer_ref', 'occurred_at'),
        Index('idx_audit_payment_ref_time', 'payment_ref', 'occurred_at'),
        Index('idx_audit_payment_order', 'payment_order_id'),
        Index('idx_audit_correlation', 'correlation_id'),
        Index('idx_audit_time', 'occurred_at'),
        Index('idx_audit_type_time', 'event_type', 'occurred_at'),
    )

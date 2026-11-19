"""Notification and service status models"""
import uuid
from datetime import UTC, datetime

from sqlalchemy import CheckConstraint, DateTime, ForeignKey, Index, Integer, String, UniqueConstraint, Uuid
from sqlalchemy.orm import Mapped, mapped_column

from ..database import Base


class CustomerNotification(Base):
    """Customer notification outbox (FR-006, FR-008, NFR-028, NFR-033, NFR-047)"""
    __tablename__ = "customer_notification"

    customer_notification_id: Mapped[uuid.UUID] = mapped_column(Uuid, primary_key=True, default=uuid.uuid4)
    customer_id: Mapped[uuid.UUID] = mapped_column(Uuid, ForeignKey("customer.customer_id"), nullable=False)
    payment_order_id: Mapped[uuid.UUID | None] = mapped_column(Uuid, ForeignKey("payment_order.payment_order_id"), nullable=True)
    notification_type: Mapped[str] = mapped_column(String(32), nullable=False)
    channel: Mapped[str] = mapped_column(String(16), nullable=False)
    template_code: Mapped[str] = mapped_column(String(64), nullable=False)
    title: Mapped[str] = mapped_column(String(140), nullable=False)
    body_summary: Mapped[str] = mapped_column(String(500), nullable=False)
    delivery_state: Mapped[str] = mapped_column(String(16), nullable=False, default='queued')
    read_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    dispatched_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    provider_reference: Mapped[str | None] = mapped_column(String(128), nullable=True)
    correlation_id: Mapped[str] = mapped_column(String(128), nullable=False)
    payload_digest: Mapped[str | None] = mapped_column(String(128), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, default=lambda: datetime.now(UTC))
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, default=lambda: datetime.now(UTC), onupdate=lambda: datetime.now(UTC))

    __table_args__ = (
        CheckConstraint(
            "notification_type IN ('sign_in_event', 'device_change', 'credential_recovery', 'payment_sent', 'payment_pending', 'payment_failed', 'payment_held', 'scam_claim_update', 'service_incident')",
            name='ck_cn_type'
        ),
        CheckConstraint("channel IN ('in_app', 'push', 'sms', 'email')", name='ck_cn_channel'),
        CheckConstraint("delivery_state IN ('queued', 'sent', 'delivered', 'failed', 'suppressed')", name='ck_cn_delivery'),
        Index('idx_cn_customer_dispatched', 'customer_id', 'dispatched_at'),
        Index('idx_cn_order_delivery', 'payment_order_id', 'delivery_state'),
    )


class NotificationDeliveryAttempt(Base):
    """Notification delivery retry tracking (FR-008, FR-009, NFR-047, NFR-065, NFR-067)"""
    __tablename__ = "notification_delivery_attempt"

    notification_delivery_attempt_id: Mapped[uuid.UUID] = mapped_column(Uuid, primary_key=True, default=uuid.uuid4)
    customer_notification_id: Mapped[uuid.UUID] = mapped_column(Uuid, ForeignKey("customer_notification.customer_notification_id"), nullable=False)
    attempt_number: Mapped[int] = mapped_column(Integer, nullable=False)
    outcome: Mapped[str] = mapped_column(String(16), nullable=False)
    provider_response_code: Mapped[str | None] = mapped_column(String(64), nullable=True)
    attempted_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, default=lambda: datetime.now(UTC))

    __table_args__ = (
        UniqueConstraint('customer_notification_id', 'attempt_number', name='uq_nda_notification_attempt'),
        CheckConstraint("attempt_number >= 1", name='ck_nda_attempt'),
        CheckConstraint("outcome IN ('sent', 'delivered', 'failed', 'timeout')", name='ck_nda_outcome'),
        Index('idx_notification_attempt_notification', 'customer_notification_id', 'attempted_at'),
    )


class ScamClaim(Base):
    """Scam claim reporting (FR-006, NFR-033, NFR-035, NFR-058, NFR-059)"""
    __tablename__ = "scam_claim"

    scam_claim_id: Mapped[uuid.UUID] = mapped_column(Uuid, primary_key=True, default=uuid.uuid4)
    customer_id: Mapped[uuid.UUID] = mapped_column(Uuid, ForeignKey("customer.customer_id"), nullable=False)
    payment_order_id: Mapped[uuid.UUID | None] = mapped_column(Uuid, ForeignKey("payment_order.payment_order_id"), nullable=True)
    claim_reference: Mapped[str] = mapped_column(String(32), nullable=False, unique=True)
    claim_status: Mapped[str] = mapped_column(String(16), nullable=False, default='reported')
    claim_reason_code: Mapped[str | None] = mapped_column(String(64), nullable=True)
    reported_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    support_case_reference: Mapped[str | None] = mapped_column(String(128), nullable=True)
    fraud_case_reference: Mapped[str | None] = mapped_column(String(128), nullable=True)
    notes_digest: Mapped[str | None] = mapped_column(String(128), nullable=True)
    correlation_id: Mapped[str] = mapped_column(String(128), nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, default=lambda: datetime.now(UTC))
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, default=lambda: datetime.now(UTC), onupdate=lambda: datetime.now(UTC))

    __table_args__ = (
        CheckConstraint("claim_status IN ('reported', 'under_review', 'closed', 'rejected', 'escalated')", name='ck_scam_claim_status'),
        Index('idx_scam_claim_customer', 'customer_id', 'reported_at'),
        Index('idx_scam_claim_order', 'payment_order_id'),
    )


class ServiceStatusNotice(Base):
    """Service degradation notice (FR-009, NFR-019, NFR-020, NFR-050)"""
    __tablename__ = "service_status_notice"

    service_status_notice_id: Mapped[uuid.UUID] = mapped_column(Uuid, primary_key=True, default=uuid.uuid4)
    capability: Mapped[str] = mapped_column(String(24), nullable=False)
    severity: Mapped[str] = mapped_column(String(12), nullable=False)
    headline: Mapped[str] = mapped_column(String(140), nullable=False)
    customer_message: Mapped[str] = mapped_column(String(500), nullable=False)
    still_available_text: Mapped[str | None] = mapped_column(String(255), nullable=True)
    next_step_text: Mapped[str | None] = mapped_column(String(255), nullable=True)
    next_update_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    starts_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    ends_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, default=lambda: datetime.now(UTC))
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, default=lambda: datetime.now(UTC), onupdate=lambda: datetime.now(UTC))

    __table_args__ = (
        CheckConstraint(
            "capability IN ('sign_in', 'accounts', 'payees', 'payments', 'notifications', 'confirmation_of_payee')",
            name='ck_ssn_capability'
        ),
        CheckConstraint("severity IN ('info', 'degraded', 'outage', 'planned')", name='ck_ssn_severity'),
        CheckConstraint("ends_at IS NULL OR ends_at > starts_at", name='ck_ssn_window'),
        Index('idx_ssn_active', 'capability', 'starts_at'),
    )

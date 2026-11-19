from datetime import datetime

from sqlalchemy import DateTime, ForeignKey, Index, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from app.common.enums import AuditEventType, AuditSeverity
from app.database import Base


class AuditLog(Base):
    """Audit log record."""
    __tablename__ = "audit_log"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    correlation_id: Mapped[str] = mapped_column(String(100), nullable=False)
    auth_session_id: Mapped[int | None] = mapped_column(Integer, ForeignKey("auth_session.id"), nullable=True)
    user_identity_id: Mapped[int | None] = mapped_column(Integer, ForeignKey("user_identity.id"), nullable=True)
    entity_type: Mapped[str | None] = mapped_column(String(50), nullable=True)
    entity_id: Mapped[str | None] = mapped_column(String(100), nullable=True)
    event_type: Mapped[str] = mapped_column(String(50), nullable=False)
    severity: Mapped[str] = mapped_column(String(20), nullable=False, default=AuditSeverity.INFO.value)
    payload_json: Mapped[str | None] = mapped_column(Text, nullable=True)
    occurred_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)

    __table_args__ = (
        Index("ix_audit_log_correlation_id", "correlation_id"),
        Index("ix_audit_log_auth_session_id", "auth_session_id"),
        Index("ix_audit_log_user_identity_id", "user_identity_id"),
        Index("ix_audit_log_entity_id", "entity_id"),
        Index("ix_audit_log_event_type", "event_type"),
        Index("ix_audit_log_occurred_at", "occurred_at"),
    )


class NotificationDispatch(Base):
    """Notification dispatch record."""
    __tablename__ = "notification_dispatch"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    payment_instruction_id: Mapped[int | None] = mapped_column(Integer, ForeignKey("payment_instruction.id"), nullable=True)
    auth_session_id: Mapped[int | None] = mapped_column(Integer, ForeignKey("auth_session.id"), nullable=True)
    notification_type: Mapped[str] = mapped_column(String(30), nullable=False)
    provider_reference: Mapped[str | None] = mapped_column(String(100), nullable=True)
    dispatch_state: Mapped[str] = mapped_column(String(20), nullable=False)
    dispatched_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)

    __table_args__ = (
        Index("ix_notification_dispatch_payment_instruction_id", "payment_instruction_id"),
        Index("ix_notification_dispatch_auth_session_id", "auth_session_id"),
    )

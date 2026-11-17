from datetime import datetime
from sqlalchemy import String, Integer, DateTime, Uuid, Text, CheckConstraint, Index, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy.sql import func
import uuid
from app.database import Base
from app.core.clock import Clock


class AuditLogEntry(Base):
    __tablename__ = "audit_log_entry"

    id: Mapped[uuid.UUID] = mapped_column(Uuid, primary_key=True)
    chain_key: Mapped[str] = mapped_column(String(64), nullable=False)
    chain_seq: Mapped[int] = mapped_column(Integer, nullable=False)
    actor_type: Mapped[str] = mapped_column(String(20), nullable=False)
    case_id: Mapped[uuid.UUID | None] = mapped_column(Uuid, ForeignKey("case_record.id"), nullable=True)
    session_id: Mapped[uuid.UUID | None] = mapped_column(Uuid, ForeignKey("orchestration_session.id"), nullable=True)
    actor_user_id: Mapped[int | None] = mapped_column(Integer, ForeignKey("app_user.id"), nullable=True)
    actor_agent_code: Mapped[str | None] = mapped_column(String(40), ForeignKey("agent_registry.agent_code"), nullable=True)
    source_component: Mapped[str] = mapped_column(String(40), nullable=False)
    event_class: Mapped[str] = mapped_column(String(40), nullable=False)
    severity: Mapped[str] = mapped_column(String(10), nullable=False, default='info')
    entity_type: Mapped[str] = mapped_column(String(40), nullable=False)
    entity_id: Mapped[str] = mapped_column(String(64), nullable=False)
    outcome_code: Mapped[str] = mapped_column(String(40), nullable=False)
    summary_text: Mapped[str] = mapped_column(String(1000), nullable=False)
    correlation_id: Mapped[str] = mapped_column(String(64), nullable=False)
    retention_class: Mapped[str] = mapped_column(String(20), nullable=False, default='regulatory')
    previous_entry_hash: Mapped[str | None] = mapped_column(String(64), nullable=True)
    entry_hash: Mapped[str] = mapped_column(String(64), nullable=False)
    occurred_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, default=Clock.utc_now, server_default=func.current_timestamp())

    __table_args__ = (
        CheckConstraint("actor_type IN ('customer', 'colleague', 'agent', 'policy_engine', 'tool_layer', 'system')", name="ck_audit_log_entry_actor_type"),
        CheckConstraint("severity IN ('info', 'warning', 'critical')", name="ck_audit_log_entry_severity"),
        CheckConstraint("retention_class IN ('regulatory', 'operational')", name="ck_audit_log_entry_retention"),
        CheckConstraint("chain_seq >= 1", name="ck_audit_log_entry_chain_seq"),
        Index("uq_audit_log_entry_chain", "chain_key", "chain_seq", unique=True),
        Index("ix_audit_log_entry_case_occurred", "case_id", "occurred_at"),
        Index("ix_audit_log_entry_correlation_id", "correlation_id", "occurred_at"),
        Index("ix_audit_log_entry_session_id", "session_id"),
        Index("ix_audit_log_entry_actor_user_id", "actor_user_id"),
        Index("ix_audit_log_entry_agent_code", "actor_agent_code"),
        Index("ix_audit_log_entry_entity", "entity_type", "entity_id"),
    )

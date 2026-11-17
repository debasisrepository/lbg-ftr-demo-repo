from datetime import datetime
from sqlalchemy import String, Integer, DateTime, Uuid, Text, Boolean, CheckConstraint, Index, ForeignKey, JSON
from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy.sql import func
import uuid
from app.database import Base
from app.core.clock import Clock


class AgentRegistry(Base):
    __tablename__ = "agent_registry"

    agent_code: Mapped[str] = mapped_column(String(40), primary_key=True)
    agent_role: Mapped[str] = mapped_column(String(40), nullable=False)
    max_autonomy_level: Mapped[int] = mapped_column(Integer, nullable=False)
    shadow_mode_default: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
    kill_switch_active: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)

    __table_args__ = (
        CheckConstraint("agent_role IN ('intake_triage', 'case_owner', 'guardrail_supervisor', 'colleague_copilot')", name="ck_agent_registry_role"),
        CheckConstraint("max_autonomy_level >= 0 AND max_autonomy_level <= 3", name="ck_agent_registry_autonomy"),
    )


class OrchestrationSession(Base):
    __tablename__ = "orchestration_session"

    id: Mapped[uuid.UUID] = mapped_column(Uuid, primary_key=True)
    thread_id: Mapped[uuid.UUID] = mapped_column(Uuid, ForeignKey("conversation_thread.id"), nullable=False)
    case_id: Mapped[uuid.UUID | None] = mapped_column(Uuid, ForeignKey("case_record.id"), nullable=True)
    trigger_type: Mapped[str] = mapped_column(String(40), nullable=False)
    state: Mapped[str] = mapped_column(String(40), nullable=False)
    entry_context_ref: Mapped[str | None] = mapped_column(String(100), nullable=True)
    status_context_shown: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, default=Clock.utc_now, server_default=func.current_timestamp())
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, default=Clock.utc_now, onupdate=Clock.utc_now, server_default=func.current_timestamp())

    __table_args__ = (
        CheckConstraint("trigger_type IN ('customer_message', 'colleague_pickup', 'callback_milestone', 'sla_timer', 'heartbeat')", name="ck_orchestration_session_trigger"),
        CheckConstraint("state IN ('started', 'classifying', 'gathering_evidence', 'awaiting_customer', 'resolved_in_scope', 'handed_off', 'failed_safe', 'closed')", name="ck_orchestration_session_state"),
        Index("ix_orchestration_session_thread_id", "thread_id"),
        Index("ix_orchestration_session_case_id", "case_id"),
    )


class OrchestrationStep(Base):
    __tablename__ = "orchestration_step"

    id: Mapped[uuid.UUID] = mapped_column(Uuid, primary_key=True)
    session_id: Mapped[uuid.UUID] = mapped_column(Uuid, ForeignKey("orchestration_session.id"), nullable=False)
    step_no: Mapped[int] = mapped_column(Integer, nullable=False)
    agent_code: Mapped[str] = mapped_column(String(40), ForeignKey("agent_registry.agent_code"), nullable=False)
    proposed_actions: Mapped[dict | None] = mapped_column(JSON, nullable=True)
    policy_decision_refs: Mapped[dict | None] = mapped_column(JSON, nullable=True)
    execution_outcomes: Mapped[dict | None] = mapped_column(JSON, nullable=True)
    occurred_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, default=Clock.utc_now, server_default=func.current_timestamp())

    __table_args__ = (
        Index("ix_orchestration_step_session_step", "session_id", "step_no"),
    )


class AgentCaseState(Base):
    __tablename__ = "agent_case_state"

    id: Mapped[uuid.UUID] = mapped_column(Uuid, primary_key=True)
    case_id: Mapped[uuid.UUID] = mapped_column(Uuid, ForeignKey("case_record.id"), nullable=False)
    agent_code: Mapped[str] = mapped_column(String(40), ForeignKey("agent_registry.agent_code"), nullable=False)
    state_json: Mapped[dict | None] = mapped_column(JSON, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, default=Clock.utc_now)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, default=Clock.utc_now, onupdate=Clock.utc_now)

    __table_args__ = (
        Index("uq_agent_case_state_case_agent", "case_id", "agent_code", unique=True),
    )

from datetime import datetime
from sqlalchemy import String, Integer, DateTime, Uuid, Text, Boolean, CheckConstraint, Index, ForeignKey, JSON
from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy.sql import func
import uuid
from app.database import Base
from app.core.clock import Clock


class ActionControl(Base):
    __tablename__ = "action_control"

    action_code: Mapped[str] = mapped_column(String(40), primary_key=True)
    action_type: Mapped[str] = mapped_column(String(20), nullable=False)
    max_autonomy_level: Mapped[int] = mapped_column(Integer, nullable=False)
    sca_required: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    changes_card_or_money: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    shadow_mode: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
    kill_switch_active: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)

    __table_args__ = (
        CheckConstraint("action_type IN ('tool', 'information', 'escalation')", name="ck_action_control_type"),
        CheckConstraint("max_autonomy_level >= 0 AND max_autonomy_level <= 3", name="ck_action_control_autonomy"),
        CheckConstraint("(changes_card_or_money = FALSE) OR (changes_card_or_money = TRUE AND sca_required = TRUE)", name="ck_action_control_sca"),
    )


class PolicyDecision(Base):
    __tablename__ = "policy_decision"

    id: Mapped[uuid.UUID] = mapped_column(Uuid, primary_key=True)
    session_id: Mapped[uuid.UUID] = mapped_column(Uuid, ForeignKey("orchestration_session.id"), nullable=False)
    action_code: Mapped[str] = mapped_column(String(40), ForeignKey("action_control.action_code"), nullable=False)
    outcome: Mapped[str] = mapped_column(String(20), nullable=False)
    reason_code: Mapped[str | None] = mapped_column(String(40), nullable=True)
    sca_reference: Mapped[str | None] = mapped_column(String(100), nullable=True)
    evaluation_context: Mapped[dict | None] = mapped_column(JSON, nullable=True)
    occurred_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, default=Clock.utc_now, server_default=func.current_timestamp())

    __table_args__ = (
        CheckConstraint("outcome IN ('approved', 'denied', 'escalate_human', 'downgrade_to_information')", name="ck_policy_decision_outcome"),
        CheckConstraint("(outcome = 'denied' AND reason_code IN ('kill_switch', 'autonomy_exceeded', 'sca_required', 'vulnerability_override', 'confidence_low', 'human_requested')) OR (outcome IN ('approved', 'escalate_human', 'downgrade_to_information'))", name="ck_policy_decision_l3"),
        Index("ix_policy_decision_session_occurred", "session_id", "occurred_at"),
    )


class ToolInvocation(Base):
    __tablename__ = "tool_invocation"

    id: Mapped[uuid.UUID] = mapped_column(Uuid, primary_key=True)
    session_id: Mapped[uuid.UUID] = mapped_column(Uuid, ForeignKey("orchestration_session.id"), nullable=False)
    action_code: Mapped[str] = mapped_column(String(40), ForeignKey("action_control.action_code"), nullable=False)
    policy_decision_id: Mapped[uuid.UUID] = mapped_column(Uuid, ForeignKey("policy_decision.id"), nullable=False)
    execution_mode: Mapped[str] = mapped_column(String(20), nullable=False)
    input_params: Mapped[dict | None] = mapped_column(JSON, nullable=True)
    token_scope_ref: Mapped[str | None] = mapped_column(String(100), nullable=True)
    token_expires_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    outcome: Mapped[str] = mapped_column(String(20), nullable=False)
    result_summary: Mapped[str | None] = mapped_column(Text, nullable=True)
    invoked_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, default=Clock.utc_now, server_default=func.current_timestamp())

    __table_args__ = (
        CheckConstraint("execution_mode IN ('proposed', 'shadow_executed', 'executed')", name="ck_tool_invocation_mode"),
        CheckConstraint("outcome IN ('success', 'failure', 'timeout', 'sca_failed')", name="ck_tool_invocation_outcome"),
        Index("ix_tool_invocation_session_invoked", "session_id", "invoked_at"),
    )

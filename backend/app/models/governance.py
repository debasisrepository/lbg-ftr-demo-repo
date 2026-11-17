"""Governance models."""
import uuid
from datetime import datetime

from sqlalchemy import CheckConstraint, DateTime, Index, String, Text, Uuid
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy.types import JSON

from app.database import Base


class PolicyDecision(Base):
    """Policy decision record."""

    __tablename__ = "policy_decisions"

    id: Mapped[uuid.UUID] = mapped_column(Uuid, primary_key=True, default=uuid.uuid4)
    decision_scope: Mapped[str] = mapped_column(String(100), nullable=False, index=True)
    case_id: Mapped[uuid.UUID | None] = mapped_column(Uuid, nullable=True, index=True)
    entity_type: Mapped[str | None] = mapped_column(String(100), nullable=True)
    entity_id: Mapped[str | None] = mapped_column(String(255), nullable=True)
    outcome: Mapped[str] = mapped_column(String(50), nullable=False)
    denial_reason_code: Mapped[str | None] = mapped_column(String(100), nullable=True)
    decision_metadata_json: Mapped[dict | None] = mapped_column(
        JSON().with_variant(JSONB(), "postgresql"), nullable=True
    )
    correlation_id: Mapped[str | None] = mapped_column(String(255), nullable=True, index=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)

    __table_args__ = (
        CheckConstraint(
            "decision_scope IN ('eligibility', 'continuity', 'colleague_retrieval', 'protected_action')",
            name="ck_decision_scope",
        ),
        CheckConstraint(
            "outcome IN ('permitted', 'denied')",
            name="ck_outcome",
        ),
        Index("ix_policy_decision_scope_created", decision_scope, created_at),
    )


class AgentExecutionRecord(Base):
    """Agent execution record."""

    __tablename__ = "agent_execution_records"

    id: Mapped[uuid.UUID] = mapped_column(Uuid, primary_key=True, default=uuid.uuid4)
    agent_name: Mapped[str] = mapped_column(String(100), nullable=False, index=True)
    case_id: Mapped[uuid.UUID | None] = mapped_column(Uuid, nullable=True, index=True)
    purpose: Mapped[str | None] = mapped_column(Text, nullable=True)
    execution_mode: Mapped[str] = mapped_column(String(50), nullable=False)
    output_summary: Mapped[str | None] = mapped_column(Text, nullable=True)
    execution_duration_ms: Mapped[int | None] = mapped_column(nullable=True)
    correlation_id: Mapped[str | None] = mapped_column(String(255), nullable=True, index=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)


class ToolInvocationRecord(Base):
    """Tool invocation record."""

    __tablename__ = "tool_invocation_records"

    id: Mapped[uuid.UUID] = mapped_column(Uuid, primary_key=True, default=uuid.uuid4)
    tool_name: Mapped[str] = mapped_column(String(100), nullable=False, index=True)
    case_id: Mapped[uuid.UUID | None] = mapped_column(Uuid, nullable=True, index=True)
    request_summary: Mapped[str | None] = mapped_column(Text, nullable=True)
    external_response_reference: Mapped[str | None] = mapped_column(String(255), nullable=True)
    tool_credential_scope: Mapped[str] = mapped_column(String(50), nullable=False, default="customer")
    execution_duration_ms: Mapped[int | None] = mapped_column(nullable=True)
    correlation_id: Mapped[str | None] = mapped_column(String(255), nullable=True, index=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)

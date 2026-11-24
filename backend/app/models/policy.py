"""Policy and rule models."""
import uuid
from datetime import datetime

from sqlalchemy import (
    JSON,
    Boolean,
    CheckConstraint,
    DateTime,
    ForeignKey,
    Index,
    Integer,
    String,
    Uuid,
)
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column

from app.core.db import Base


class PolicyRuleSetVersion(Base):
    """Policy rule set version."""

    __tablename__ = "policy_rule_set_versions"

    id: Mapped[uuid.UUID] = mapped_column(Uuid, primary_key=True, default=uuid.uuid4)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)

    version_number: Mapped[int] = mapped_column(Integer, nullable=False, unique=True, index=True)
    version_label: Mapped[str] = mapped_column(String(100), nullable=False)
    region_code: Mapped[str] = mapped_column(String(50), nullable=False, default="ALL", index=True)
    rule_set_status: Mapped[str] = mapped_column(String(50), nullable=False, index=True)
    effective_from: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    effective_to: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    approved_by_user_id: Mapped[uuid.UUID | None] = mapped_column(Uuid, ForeignKey("users.id"), nullable=True, index=True)
    approved_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    change_note: Mapped[str | None] = mapped_column(String(1000), nullable=True)

    __table_args__ = (
        CheckConstraint("rule_set_status IN ('draft', 'active', 'superseded', 'archived')", name="ck_policy_rule_set_versions_status"),
    )


class PolicyRule(Base):
    """Individual policy rule within a rule set version."""

    __tablename__ = "policy_rules"

    id: Mapped[uuid.UUID] = mapped_column(Uuid, primary_key=True, default=uuid.uuid4)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)

    rule_set_version_id: Mapped[uuid.UUID | None] = mapped_column(
        Uuid, ForeignKey("policy_rule_set_versions.id"), nullable=True, index=True
    )
    rule_code: Mapped[str] = mapped_column(String(100), nullable=False, index=True)
    rule_category: Mapped[str] = mapped_column(String(50), nullable=False)
    action_type: Mapped[str] = mapped_column(String(50), nullable=False, index=True)
    rule_description: Mapped[str] = mapped_column(String(500), nullable=False)
    condition_json: Mapped[dict] = mapped_column(
        JSON().with_variant(JSONB(), "postgresql"), nullable=False
    )
    parameters_json: Mapped[dict] = mapped_column(
        JSON().with_variant(JSONB(), "postgresql"), nullable=False, default=dict
    )
    failure_message: Mapped[str] = mapped_column(String(255), nullable=False)
    evaluation_order: Mapped[int] = mapped_column(Integer, nullable=False)
    is_enabled: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)

    __table_args__ = (
        CheckConstraint("action_type IN ('promise_create', 'queue_entry', 'approval_request')", name="ck_policy_rules_action_type"),
        Index("uq_policy_rules_version_code", "rule_set_version_id", "rule_code", unique=True),
        Index("ix_policy_rules_action_enabled", "action_type", "is_enabled"),
    )


class PolicyEvaluationRecord(Base):
    """Record of policy evaluation."""

    __tablename__ = "policy_evaluation_records"

    id: Mapped[uuid.UUID] = mapped_column(Uuid, primary_key=True, default=uuid.uuid4)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)

    rule_set_version_id: Mapped[uuid.UUID | None] = mapped_column(
        Uuid, ForeignKey("policy_rule_set_versions.id"), nullable=True, index=True
    )
    evaluation_context_type: Mapped[str] = mapped_column(String(50), nullable=False, index=True)
    action_type: Mapped[str] = mapped_column(String(50), nullable=False, index=True)
    subject_entity_type: Mapped[str] = mapped_column(String(50), nullable=False)
    subject_entity_id: Mapped[uuid.UUID | None] = mapped_column(Uuid, nullable=True, index=True)
    actor_user_id: Mapped[uuid.UUID | None] = mapped_column(Uuid, ForeignKey("users.id"), nullable=True, index=True)
    actor_role_code: Mapped[str | None] = mapped_column(String(50), nullable=True)
    evaluation_result: Mapped[str] = mapped_column(String(50), nullable=False, index=True)
    failed_condition_code: Mapped[str | None] = mapped_column(String(100), nullable=True)
    failed_conditions_json: Mapped[dict] = mapped_column(
        JSON().with_variant(JSONB(), "postgresql"), nullable=False, default=dict
    )
    rules_applied_json: Mapped[dict] = mapped_column(
        JSON().with_variant(JSONB(), "postgresql"), nullable=False, default=dict
    )
    input_snapshot_json: Mapped[dict] = mapped_column(
        JSON().with_variant(JSONB(), "postgresql"), nullable=False, default=dict
    )
    evaluated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, index=True)
    evaluated_by_component: Mapped[str] = mapped_column(String(100), nullable=False)
    correlation_id: Mapped[str | None] = mapped_column(String(36), nullable=True, index=True)

    __table_args__ = (
        CheckConstraint("evaluation_result IN ('pass', 'fail')", name="ck_policy_evaluation_records_result"),
        Index("ix_policy_evaluation_records_entity", "subject_entity_type", "subject_entity_id"),
    )

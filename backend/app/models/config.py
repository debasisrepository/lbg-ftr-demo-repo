"""Configuration and reference data models."""
import uuid
from datetime import datetime

from sqlalchemy import CheckConstraint, DateTime, Integer, String, Text, Uuid
from sqlalchemy.orm import Mapped, mapped_column

from app.database import Base


class IssueEligibilityRule(Base):
    """Issue type eligibility rules for case creation."""

    __tablename__ = "issue_eligibility_rules"

    id: Mapped[uuid.UUID] = mapped_column(Uuid, primary_key=True, default=uuid.uuid4)
    issue_type: Mapped[str] = mapped_column(String(100), nullable=False, unique=True, index=True)
    is_eligible: Mapped[bool] = mapped_column(nullable=False)
    redirect_journey_code: Mapped[str | None] = mapped_column(String(100), nullable=True)
    priority_weight: Mapped[int] = mapped_column(Integer, default=100, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)


class CaseLifecycleTransition(Base):
    """Allowed case lifecycle state transitions."""

    __tablename__ = "case_lifecycle_transitions"

    id: Mapped[uuid.UUID] = mapped_column(Uuid, primary_key=True, default=uuid.uuid4)
    from_state: Mapped[str] = mapped_column(String(50), nullable=False)
    to_state: Mapped[str] = mapped_column(String(50), nullable=False)
    basis_type: Mapped[str] = mapped_column(String(50), nullable=False)
    is_active: Mapped[bool] = mapped_column(default=True, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)

    __table_args__ = (CheckConstraint("from_state <> to_state", name="ck_transition_different_states"),)


class OwnerTeamMapping(Base):
    """Owner team code to display name mapping."""

    __tablename__ = "owner_team_mappings"

    id: Mapped[uuid.UUID] = mapped_column(Uuid, primary_key=True, default=uuid.uuid4)
    owner_team_code: Mapped[str] = mapped_column(String(100), nullable=False, unique=True, index=True)
    owner_semantic_label: Mapped[str] = mapped_column(String(100), nullable=False)
    owner_display_name: Mapped[str] = mapped_column(String(255), nullable=False)
    is_active: Mapped[bool] = mapped_column(default=True, nullable=False)
    superseded_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)


class KillSwitchSetting(Base):
    """Agent and tool kill switch configuration."""

    __tablename__ = "kill_switch_settings"

    id: Mapped[uuid.UUID] = mapped_column(Uuid, primary_key=True, default=uuid.uuid4)
    component_type: Mapped[str] = mapped_column(String(20), nullable=False)  # agent or tool
    component_name: Mapped[str] = mapped_column(String(100), nullable=False, index=True)
    is_enabled: Mapped[bool] = mapped_column(default=True, nullable=False)
    execution_mode: Mapped[str] = mapped_column(
        String(20), nullable=False, default="active"
    )  # active, recommend_only, read_only, shadow, disabled
    disabled_reason: Mapped[str | None] = mapped_column(Text, nullable=True)
    disabled_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, onupdate=lambda: datetime.now(datetime.now().tzinfo or None)
    )

    __table_args__ = (CheckConstraint("component_type IN ('agent', 'tool')", name="ck_component_type"),)

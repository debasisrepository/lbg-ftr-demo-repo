"""Role profile and assignment models."""
import uuid
from datetime import datetime

from sqlalchemy import JSON, CheckConstraint, DateTime, ForeignKey, Index, String, Uuid
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column

from app.core.db import Base


class RoleProfile(Base):
    """Role profile defining permissions and entitlements."""

    __tablename__ = "role_profiles"

    id: Mapped[uuid.UUID] = mapped_column(Uuid, primary_key=True, default=uuid.uuid4)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)

    role_code: Mapped[str] = mapped_column(String(50), nullable=False, unique=True, index=True)
    role_label: Mapped[str] = mapped_column(String(100), nullable=False)
    description: Mapped[str | None] = mapped_column(String(500), nullable=True)
    allowed_widgets_json: Mapped[dict] = mapped_column(
        JSON().with_variant(JSONB(), "postgresql"), nullable=False, default=dict
    )
    entitled_queue_states_json: Mapped[dict] = mapped_column(
        JSON().with_variant(JSONB(), "postgresql"), nullable=False, default=dict
    )
    allowed_actions_json: Mapped[dict] = mapped_column(
        JSON().with_variant(JSONB(), "postgresql"), nullable=False, default=dict
    )
    can_view_sensitive_fields: Mapped[bool] = mapped_column(nullable=False, default=False)
    profile_status: Mapped[str] = mapped_column(String(50), nullable=False, default="active")

    __table_args__ = (
        CheckConstraint("profile_status IN ('active', 'deprecated', 'archived')", name="ck_role_profiles_status"),
    )


class RoleAssignment(Base):
    """Assignment of role to user with scope and temporal validity."""

    __tablename__ = "role_assignments"

    id: Mapped[uuid.UUID] = mapped_column(Uuid, primary_key=True, default=uuid.uuid4)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)

    user_id: Mapped[uuid.UUID] = mapped_column(Uuid, ForeignKey("users.id"), nullable=False, index=True)
    role_code: Mapped[str] = mapped_column(String(50), ForeignKey("role_profiles.role_code"), nullable=False, index=True)
    scope_type: Mapped[str | None] = mapped_column(String(50), nullable=True)
    scope_value: Mapped[str | None] = mapped_column(String(255), nullable=True)
    effective_from: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    effective_to: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    assignment_status: Mapped[str] = mapped_column(String(50), nullable=False, default="active")

    __table_args__ = (
        CheckConstraint("assignment_status IN ('active', 'suspended', 'revoked')", name="ck_role_assignments_status"),
        Index("ix_role_assignments_user_role", "user_id", "role_code"),
    )

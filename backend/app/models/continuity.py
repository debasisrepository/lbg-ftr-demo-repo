"""Continuity models."""
import uuid
from datetime import datetime

from sqlalchemy import Boolean, CheckConstraint, DateTime, Index, String, Uuid
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy.types import JSON

from app.database import Base


class ContinuityContext(Base):
    """Structured continuity context for case."""

    __tablename__ = "continuity_contexts"

    id: Mapped[uuid.UUID] = mapped_column(Uuid, primary_key=True, default=uuid.uuid4)
    case_id: Mapped[uuid.UUID] = mapped_column(Uuid, nullable=False, index=True)
    package_version: Mapped[int] = mapped_column(default=1, nullable=False)
    structured_context_json: Mapped[dict] = mapped_column(JSON().with_variant(JSONB(), "postgresql"), nullable=False)
    llm_safe_payload_json: Mapped[dict] = mapped_column(JSON().with_variant(JSONB(), "postgresql"), nullable=False)
    colleague_payload_json: Mapped[dict] = mapped_column(JSON().with_variant(JSONB(), "postgresql"), nullable=False)
    restricted_fields_excluded_flag: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    last_channel: Mapped[str | None] = mapped_column(String(50), nullable=True)
    last_presented_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    effective_from: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    effective_to: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    is_current: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)

    __table_args__ = (
        Index(
            "ix_continuity_case_current",
            case_id,
            postgresql_where=(is_current == True),  # noqa: E712
            sqlite_where=(is_current == True),  # noqa: E712
            unique=True,
        ),
    )


class ChannelHandoff(Base):
    """Channel handoff record (append-only)."""

    __tablename__ = "channel_handoffs"

    id: Mapped[uuid.UUID] = mapped_column(Uuid, primary_key=True, default=uuid.uuid4)
    case_id: Mapped[uuid.UUID] = mapped_column(Uuid, nullable=False, index=True)
    from_channel: Mapped[str] = mapped_column(String(50), nullable=False)
    to_channel: Mapped[str] = mapped_column(String(50), nullable=False)
    context_presented_flag: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    handoff_timestamp: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, index=True)
    correlation_id: Mapped[str | None] = mapped_column(String(255), nullable=True, index=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)

    __table_args__ = (
        CheckConstraint(
            "from_channel IN ('mobile_app', 'chat', 'phone', 'branch', 'colleague_desktop', 'ai_assistant')",
            name="ck_from_channel",
        ),
        CheckConstraint(
            "to_channel IN ('mobile_app', 'chat', 'phone', 'branch', 'colleague_desktop', 'ai_assistant')",
            name="ck_to_channel",
        ),
    )

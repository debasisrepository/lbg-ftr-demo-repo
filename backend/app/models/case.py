"""Case core models."""
import uuid
from datetime import datetime

from sqlalchemy import (
    Boolean,
    CheckConstraint,
    DateTime,
    Index,
    String,
    Text,
    Uuid,
)
from sqlalchemy.orm import Mapped, mapped_column

from app.database import Base


class Case(Base):
    """Customer-visible case projection."""

    __tablename__ = "cases"

    id: Mapped[uuid.UUID] = mapped_column(Uuid, primary_key=True, default=uuid.uuid4)
    case_reference: Mapped[str] = mapped_column(String(32), nullable=False, unique=True, index=True)
    customer_party_id: Mapped[str] = mapped_column(String(255), nullable=False, index=True)
    brand: Mapped[str] = mapped_column(String(50), nullable=False)
    issue_type: Mapped[str] = mapped_column(String(100), nullable=False)
    classification_source: Mapped[str] = mapped_column(String(50), nullable=False)
    issue_title: Mapped[str | None] = mapped_column(String(500), nullable=True)
    issue_summary: Mapped[str | None] = mapped_column(Text, nullable=True)
    origin_channel: Mapped[str] = mapped_column(String(50), nullable=False)
    current_lifecycle_state: Mapped[str] = mapped_column(String(50), nullable=False)
    current_status_code: Mapped[str] = mapped_column(String(100), nullable=False)
    current_status_label: Mapped[str] = mapped_column(String(255), nullable=False)
    latest_meaningful_update_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    opened_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    closed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    outcome_summary: Mapped[str | None] = mapped_column(Text, nullable=True)
    retention_category: Mapped[str] = mapped_column(String(50), nullable=False, default="standard")
    continuity_state: Mapped[str] = mapped_column(String(50), nullable=False, default="current")
    complaint_sensitive_flag: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    fraud_sensitive_flag: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    vulnerable_customer_flag: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, onupdate=lambda: datetime.now(datetime.now().tzinfo or None)
    )

    __table_args__ = (
        Index("ix_cases_customer_opened", customer_party_id, opened_at),
        CheckConstraint("brand IN ('lloyds', 'bank_of_scotland')", name="ck_case_brand"),
        CheckConstraint("retention_category IN ('standard', 'regulatory', 'litigation')", name="ck_retention_category"),
        CheckConstraint("continuity_state IN ('current', 'refresh_pending', 'refreshing')", name="ck_continuity_state"),
    )


class CaseAnchorLink(Base):
    """Anchor link to system of record."""

    __tablename__ = "case_anchor_links"

    id: Mapped[uuid.UUID] = mapped_column(Uuid, primary_key=True, default=uuid.uuid4)
    case_id: Mapped[uuid.UUID] = mapped_column(Uuid, nullable=False, index=True)
    anchor_domain: Mapped[str] = mapped_column(String(100), nullable=False)
    anchor_system: Mapped[str] = mapped_column(String(100), nullable=False)
    anchor_record_type: Mapped[str] = mapped_column(String(100), nullable=False)
    anchor_record_id: Mapped[str] = mapped_column(String(255), nullable=False)
    anchor_reference: Mapped[str] = mapped_column(String(255), nullable=False, index=True)
    link_status: Mapped[str] = mapped_column(String(50), nullable=False, default="active")
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    last_synced_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)


class CaseStatusProjection(Base):
    """Time-bounded case status projection."""

    __tablename__ = "case_status_projections"

    id: Mapped[uuid.UUID] = mapped_column(Uuid, primary_key=True, default=uuid.uuid4)
    case_id: Mapped[uuid.UUID] = mapped_column(Uuid, nullable=False, index=True)
    status_code: Mapped[str] = mapped_column(String(100), nullable=False)
    status_label: Mapped[str] = mapped_column(String(255), nullable=False)
    lifecycle_state: Mapped[str] = mapped_column(String(50), nullable=False)
    status_icon: Mapped[str | None] = mapped_column(String(50), nullable=True)
    status_color: Mapped[str | None] = mapped_column(String(50), nullable=True)
    customer_facing_text: Mapped[str | None] = mapped_column(Text, nullable=True)
    next_step_text: Mapped[str | None] = mapped_column(Text, nullable=True)
    source_event_id: Mapped[uuid.UUID | None] = mapped_column(Uuid, nullable=True)
    effective_from: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    effective_to: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    is_current: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)

    __table_args__ = (
        Index(
            "ix_case_status_proj_case_current",
            case_id,
            postgresql_where=(is_current == True),  # noqa: E712
            sqlite_where=(is_current == True),  # noqa: E712
            unique=True,
        ),
        Index("ix_case_status_proj_case_effective", case_id, effective_from),
    )

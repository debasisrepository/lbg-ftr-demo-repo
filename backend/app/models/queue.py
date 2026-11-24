"""Queue and prioritization models."""
import uuid
from datetime import datetime
from decimal import Decimal
from typing import TYPE_CHECKING

from sqlalchemy import (
    JSON,
    Boolean,
    CheckConstraint,
    DateTime,
    ForeignKey,
    Index,
    Integer,
    Numeric,
    String,
    Uuid,
)
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.db import Base

if TYPE_CHECKING:
    from app.models.receivables import ReceivableItem


class QueueItem(Base):
    """Work queue item for collections."""

    __tablename__ = "queue_items"

    id: Mapped[uuid.UUID] = mapped_column(Uuid, primary_key=True, default=uuid.uuid4)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)

    receivable_item_id: Mapped[uuid.UUID] = mapped_column(Uuid, ForeignKey("receivable_items.id"), nullable=False, index=True)
    customer_account_id: Mapped[uuid.UUID] = mapped_column(Uuid, ForeignKey("customer_accounts.id"), nullable=False, index=True)
    queue_type: Mapped[str] = mapped_column(String(50), nullable=False, default="standard_collections")
    queue_state: Mapped[str] = mapped_column(String(50), nullable=False, index=True)
    is_non_standard: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False, index=True)  # type: ignore
    non_standard_reason: Mapped[str | None] = mapped_column(String(255), nullable=True)
    assigned_user_id: Mapped[uuid.UUID | None] = mapped_column(Uuid, ForeignKey("users.id"), nullable=True, index=True)
    assigned_team_ref: Mapped[str | None] = mapped_column(String(50), nullable=True, index=True)
    entered_queue_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, index=True)
    age_in_status_days: Mapped[int | None] = mapped_column(Integer, nullable=True)
    current_rank: Mapped[int | None] = mapped_column(Integer, nullable=True, index=True)
    current_priority_score: Mapped[Decimal | None] = mapped_column(Numeric(10, 2), nullable=True, index=True)
    last_refreshed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    last_sync_run_id: Mapped[uuid.UUID | None] = mapped_column(Uuid, ForeignKey("sap_sync_runs.id"), nullable=True, index=True)

    # Relationships
    receivable_item: Mapped["ReceivableItem"] = relationship("ReceivableItem", lazy="joined", foreign_keys=[receivable_item_id])

    __table_args__ = (
        CheckConstraint("queue_state IN ('active', 'awaiting_follow_up', 'blocked', 'completed', 'removed')", name="ck_queue_items_state"),
        Index("ix_queue_items_state_rank", "queue_state", "current_rank"),
    )


class PrioritizationAssessment(Base):
    """Priority assessment for queue item."""

    __tablename__ = "prioritization_assessments"

    id: Mapped[uuid.UUID] = mapped_column(Uuid, primary_key=True, default=uuid.uuid4)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)

    queue_item_id: Mapped[uuid.UUID] = mapped_column(Uuid, ForeignKey("queue_items.id"), nullable=False, index=True)
    priority_score: Mapped[Decimal] = mapped_column(Numeric(10, 2), nullable=False)
    priority_rank: Mapped[int] = mapped_column(Integer, nullable=False)
    assessment_version: Mapped[str | None] = mapped_column(String(50), nullable=True)
    assessed_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    factor_summary_json: Mapped[dict] = mapped_column(
        JSON().with_variant(JSONB(), "postgresql"), nullable=False, default=dict
    )
    promise_status_factor: Mapped[str | None] = mapped_column(String(50), nullable=True)
    actionability_status: Mapped[str | None] = mapped_column(String(50), nullable=True)
    policy_evaluation_record_id: Mapped[uuid.UUID | None] = mapped_column(
        Uuid, ForeignKey("policy_evaluation_records.id"), nullable=True, index=True
    )

    __table_args__ = (
        Index("ix_prioritization_assessments_queue_time", "queue_item_id", "assessed_at"),
    )


class InteractionLogEntry(Base):
    """Customer interaction log."""

    __tablename__ = "interaction_log_entries"

    id: Mapped[uuid.UUID] = mapped_column(Uuid, primary_key=True, default=uuid.uuid4)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)

    customer_account_id: Mapped[uuid.UUID] = mapped_column(Uuid, ForeignKey("customer_accounts.id"), nullable=False, index=True)
    interaction_type: Mapped[str] = mapped_column(String(50), nullable=False, index=True)
    interaction_direction: Mapped[str] = mapped_column(String(50), nullable=False)
    interaction_channel: Mapped[str] = mapped_column(String(50), nullable=False)
    occurred_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, index=True)
    recorded_by_user_id: Mapped[uuid.UUID | None] = mapped_column(Uuid, ForeignKey("users.id"), nullable=True, index=True)
    summary_text: Mapped[str | None] = mapped_column(String(1000), nullable=True)
    external_message_ref: Mapped[str | None] = mapped_column(String(255), nullable=True)

    __table_args__ = (
        CheckConstraint("interaction_type IN ('call', 'email', 'letter', 'portal_message', 'note')", name="ck_interaction_log_entries_type"),
        CheckConstraint("interaction_direction IN ('inbound', 'outbound', 'internal')", name="ck_interaction_log_entries_direction"),
        Index("ix_interaction_log_entries_account_time", "customer_account_id", "occurred_at"),
    )

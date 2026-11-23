"""
ScamCheckOutcome model - fraud decision and warning handling.
Requirement: REQ-PAY-006, REQ-PAY-007
"""
import uuid
from datetime import UTC, datetime

from sqlalchemy import (
    JSON,
    Boolean,
    CheckConstraint,
    DateTime,
    ForeignKey,
    Index,
    Integer,
    String,
    UniqueConstraint,
)
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column

from app.database import Base


class ScamCheckOutcome(Base):
    """
    Scam check outcome - fraud decision, warning presentation, customer decision.
    Requirement: FR-PAY-009, FR-PAY-010, FR-PAY-011
    """
    __tablename__ = "scam_check_outcomes"
    
    id: Mapped[uuid.UUID] = mapped_column(
        primary_key=True,
        default=uuid.uuid4
    )
    payment_intent_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("payment_intents.id", ondelete="CASCADE"),
        nullable=False,
        index=True
    )
    review_version: Mapped[int] = mapped_column(
        Integer,
        nullable=False
    )
    fraud_engine_reference: Mapped[str | None] = mapped_column(
        String(128),
        nullable=True
    )
    risk_outcome: Mapped[str] = mapped_column(
        String(12),
        nullable=False
    )
    decision_inputs: Mapped[dict] = mapped_column(
        JSON().with_variant(JSONB, "postgresql"),
        nullable=False
    )
    decision_latency_ms: Mapped[int | None] = mapped_column(
        Integer,
        nullable=True
    )
    customer_warning_required: Mapped[bool] = mapped_column(
        Boolean,
        nullable=False,
        default=False
    )
    policy_allows_continue: Mapped[bool] = mapped_column(
        Boolean,
        nullable=False,
        default=False
    )
    customer_warning_presented_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True
    )
    customer_decision: Mapped[str] = mapped_column(
        String(14),
        nullable=False,
        default="not_applicable"
    )
    customer_decision_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True
    )
    hold_latest_decision_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True
    )
    correlation_id: Mapped[str] = mapped_column(
        String(64),
        nullable=False,
        index=True
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        default=lambda: datetime.now(UTC)
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        default=lambda: datetime.now(UTC),
        onupdate=lambda: datetime.now(UTC)
    )
    
    __table_args__ = (
        CheckConstraint(
            "review_version >= 1",
            name="ck_sco_review_version"
        ),
        CheckConstraint(
            "risk_outcome IN ('allow','warn','hold','unavailable')",
            name="ck_sco_risk_outcome"
        ),
        CheckConstraint(
            "decision_latency_ms IS NULL OR decision_latency_ms >= 0",
            name="ck_sco_latency"
        ),
        CheckConstraint(
            "customer_decision IN ('not_applicable','pending','stopped','continued')",
            name="ck_sco_customer_decision"
        ),
        CheckConstraint(
            "customer_decision <> 'continued' OR (policy_allows_continue = TRUE AND customer_warning_presented_at IS NOT NULL)",
            name="ck_sco_continue_needs_policy"
        ),
        CheckConstraint(
            "customer_warning_required = (risk_outcome = 'warn')",
            name="ck_sco_warn_flag"
        ),
        UniqueConstraint(
            "payment_intent_id",
            "review_version",
            name="uq_sco_payment_version"
        ),
        Index("ix_sco_payment", "payment_intent_id"),
        Index("ix_sco_correlation", "correlation_id")
    )

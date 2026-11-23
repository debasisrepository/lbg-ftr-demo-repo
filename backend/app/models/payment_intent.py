"""
PaymentIntent model - canonical payment state.
Requirement: REQ-PAY-002, REQ-PAY-003
"""
import uuid
from datetime import UTC, datetime

from sqlalchemy import (
    BigInteger,
    Boolean,
    CheckConstraint,
    DateTime,
    ForeignKey,
    Integer,
    String,
    Uuid,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base


class PaymentIntent(Base):
    """
    Canonical payment intent with state machine and review tracking.
    All 23 columns as specified in task scope.
    """
    __tablename__ = "payment_intents"
    
    # Primary key
    id: Mapped[uuid.UUID] = mapped_column(Uuid, primary_key=True, default=uuid.uuid4)
    
    # Foreign keys
    customer_profile_ref_id: Mapped[uuid.UUID] = mapped_column(
        Uuid, ForeignKey("customer_profile_refs.id"), nullable=False, index=True
    )
    source_account_reference: Mapped[str] = mapped_column(String(64), nullable=False)
    payee_id: Mapped[uuid.UUID] = mapped_column(Uuid, ForeignKey("payees.id"), nullable=False, index=True)
    
    # Payment details (review fields)
    amount_minor: Mapped[int] = mapped_column(BigInteger, nullable=False)
    currency: Mapped[str] = mapped_column(String(3), nullable=False, default="GBP")
    payment_reference_text: Mapped[str] = mapped_column(String(18), nullable=False)
    
    # Channel and initiation
    payment_channel: Mapped[str] = mapped_column(String(8), nullable=False, default="mobile")
    initiation_type: Mapped[str] = mapped_column(String(24), nullable=False, default="saved_payee_payment")
    
    # Review tracking
    review_version: Mapped[int] = mapped_column(Integer, nullable=False, default=1)
    review_fingerprint: Mapped[str] = mapped_column(String(64), nullable=False)
    
    # State machine
    current_state: Mapped[str] = mapped_column(String(32), nullable=False, default="draft", index=True)
    customer_visible_status: Mapped[str | None] = mapped_column(String(8), nullable=True)
    do_not_resubmit: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    
    # Optional timestamps
    expected_arrival_time: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    payments_hub_reference: Mapped[str | None] = mapped_column(String(64), nullable=True)
    hold_latest_decision_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    customer_reviewed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    submitted_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    last_state_changed_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, default=lambda: datetime.now(UTC)
    )
    
    # Version control
    row_version: Mapped[int] = mapped_column(Integer, nullable=False, default=1)
    
    # Correlation
    correlation_id: Mapped[str | None] = mapped_column(String(64), nullable=True)
    
    # Audit timestamps
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, default=lambda: datetime.now(UTC)
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, default=lambda: datetime.now(UTC), onupdate=lambda: datetime.now(UTC)
    )
    
    # Constraints
    __table_args__ = (
        CheckConstraint("amount_minor > 0", name="ck_pi_amount_positive"),
        CheckConstraint("review_version >= 1", name="ck_pi_review_version"),
        CheckConstraint("row_version >= 1", name="ck_pi_row_version"),
        CheckConstraint(
            "length(payment_reference_text) >= 1",
            name="ck_pi_payment_reference_length"
        ),
        CheckConstraint(
            "payment_channel IN ('mobile')",
            name="ck_pi_payment_channel"
        ),
        CheckConstraint(
            "initiation_type IN ('saved_payee_payment')",
            name="ck_pi_initiation_type"
        ),
        CheckConstraint(
            """current_state IN (
                'draft', 'review_ready', 'awaiting_dynamic_link_approval',
                'approval_failed_or_abandoned', 'fraud_check_in_progress',
                'warning_presented', 'stopped_after_warning', 'held_for_review',
                'submission_in_progress', 'submitted_to_payments_hub',
                'pending_confirmation', 'completed', 'failed', 'rejected',
                'unknown_unresolved'
            )""",
            name="ck_pi_current_state"
        ),
        CheckConstraint(
            "customer_visible_status IS NULL OR customer_visible_status IN ('Sent', 'Pending', 'Failed')",
            name="ck_pi_status_mapping"
        ),
    )
    
    # Relationships
    customer = relationship("CustomerProfileRef", foreign_keys=[customer_profile_ref_id])
    payee = relationship("Payee", foreign_keys=[payee_id])

"""PaymentStatusProjection model - converged customer-visible payment status."""
import uuid
from datetime import UTC, datetime

from sqlalchemy import (
    CHAR,
    BigInteger,
    Boolean,
    CheckConstraint,
    ForeignKey,
    Index,
    String,
    UniqueConstraint,
)
from sqlalchemy.orm import Mapped, mapped_column

from app.database import Base


class PaymentStatusProjection(Base):
    """
    Payment status projections - converged customer-visible payment status.
    One status model: Sent, Pending, or Failed.
    """
    __tablename__ = "payment_status_projections"
    
    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    payment_intent_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("payment_intents.id"), nullable=False)
    customer_profile_ref_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("customer_profile_refs.id"), nullable=False)
    payment_reference_text: Mapped[str] = mapped_column(String(18), nullable=False)
    amount_minor: Mapped[int] = mapped_column(BigInteger, CheckConstraint("amount_minor > 0", name="ck_psp_amount"), nullable=False)
    currency: Mapped[str] = mapped_column(CHAR(3), default="GBP", nullable=False)
    payee_display_name: Mapped[str] = mapped_column(String(120), nullable=False)
    customer_visible_status: Mapped[str] = mapped_column(
        String(8),
        CheckConstraint("customer_visible_status IN ('Sent','Pending','Failed')", name="ck_psp_status"),
        nullable=False
    )
    held_indicator: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    unresolved_indicator: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    do_not_resubmit: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    expected_arrival_time: Mapped[datetime | None] = mapped_column(nullable=True)
    hold_latest_decision_at: Mapped[datetime | None] = mapped_column(nullable=True)
    last_event_sequence: Mapped[int] = mapped_column(BigInteger, CheckConstraint("last_event_sequence >= 0", name="ck_psp_sequence"), nullable=False)
    last_source_event_id: Mapped[str | None] = mapped_column(String(64), nullable=True)
    as_of_timestamp: Mapped[datetime] = mapped_column(default=lambda: datetime.now(UTC), nullable=False)
    freshness_status: Mapped[str] = mapped_column(
        String(14),
        CheckConstraint("freshness_status IN ('within_target','breached','unknown')", name="ck_psp_freshness"),
        default="within_target",
        nullable=False
    )
    provenance_reference: Mapped[str | None] = mapped_column(String(128), nullable=True)
    projection_updated_at: Mapped[datetime] = mapped_column(default=lambda: datetime.now(UTC), onupdate=lambda: datetime.now(UTC), nullable=False)
    
    __table_args__ = (
        UniqueConstraint('payment_intent_id', name='uq_psp_payment'),
        CheckConstraint("(customer_visible_status = 'Pending') = do_not_resubmit", name="ck_psp_pending_no_resubmit"),
        Index('ix_psp_customer', 'customer_profile_ref_id'),
        Index('ix_psp_status', 'customer_visible_status'),
        Index('ix_psp_reference', 'payment_reference_text'),
    )

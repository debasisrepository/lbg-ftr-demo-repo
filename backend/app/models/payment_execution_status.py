"""PaymentExecutionStatus model - normalized payment execution status."""
import uuid
from datetime import UTC, datetime

from sqlalchemy import (
    CheckConstraint,
    ForeignKey,
    Index,
    Integer,
    String,
    UniqueConstraint,
)
from sqlalchemy.orm import Mapped, mapped_column

from app.database import Base


class PaymentExecutionStatus(Base):
    """
    Payment execution status records - normalized status from payments hub.
    """
    __tablename__ = "payment_execution_statuses"
    
    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    payment_intent_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("payment_intents.id"), nullable=False)
    hub_submission_reference: Mapped[str | None] = mapped_column(String(64), nullable=True)
    scheme_transaction_reference: Mapped[str | None] = mapped_column(String(64), nullable=True)
    scheme_outcome: Mapped[str] = mapped_column(
        String(12),
        CheckConstraint("scheme_outcome IN ('accepted','rejected','pending','timeout','unknown')", name="ck_pes_scheme_outcome"),
        nullable=False
    )
    scheme_outcome_code: Mapped[str | None] = mapped_column(String(48), nullable=True)
    expected_arrival_time: Mapped[datetime | None] = mapped_column(nullable=True)
    hub_response_latency_ms: Mapped[int | None] = mapped_column(Integer, CheckConstraint("hub_response_latency_ms >= 0", name="ck_pes_latency"), nullable=True)
    submission_attempt_count: Mapped[int] = mapped_column(Integer, CheckConstraint("submission_attempt_count >= 0", name="ck_pes_attempts"), default=0, nullable=False)
    last_submission_error: Mapped[str | None] = mapped_column(String(128), nullable=True)
    final_indicator: Mapped[bool] = mapped_column(default=False, nullable=False)
    provenance_reference: Mapped[str | None] = mapped_column(String(128), nullable=True)
    correlation_id: Mapped[str | None] = mapped_column(String(64), nullable=True)
    received_at: Mapped[datetime] = mapped_column(default=lambda: datetime.now(UTC), nullable=False)
    created_at: Mapped[datetime] = mapped_column(default=lambda: datetime.now(UTC), nullable=False)
    updated_at: Mapped[datetime] = mapped_column(default=lambda: datetime.now(UTC), onupdate=lambda: datetime.now(UTC), nullable=False)
    
    __table_args__ = (
        UniqueConstraint('payment_intent_id', name='uq_pes_payment'),
        Index('ix_pes_hub_ref', 'hub_submission_reference'),
        Index('ix_pes_scheme_ref', 'scheme_transaction_reference'),
        Index('ix_pes_correlation', 'correlation_id'),
    )

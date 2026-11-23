"""
IdempotencyRecord model - duplicate-prevention tracking.
Requirement: REQ-PAY-002, REQ-PAY-003
"""
import uuid
from datetime import UTC, datetime

from sqlalchemy import (
    CheckConstraint,
    DateTime,
    ForeignKey,
    Integer,
    String,
    UniqueConstraint,
    Uuid,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base


class IdempotencyRecord(Base):
    """
    Idempotency record for retriable payment operations.
    All columns as specified in task scope.
    """
    __tablename__ = "idempotency_records"
    
    # Primary key
    id: Mapped[uuid.UUID] = mapped_column(Uuid, primary_key=True, default=uuid.uuid4)
    
    # Foreign keys
    customer_profile_ref_id: Mapped[uuid.UUID] = mapped_column(
        Uuid, ForeignKey("customer_profile_refs.id"), nullable=False, index=True
    )
    payment_intent_id: Mapped[uuid.UUID] = mapped_column(
        Uuid, ForeignKey("payment_intents.id"), nullable=False, index=True
    )
    
    # Idempotency fields
    operation_type: Mapped[str] = mapped_column(String(16), nullable=False)
    idempotency_key: Mapped[str] = mapped_column(String(64), nullable=False, index=True)
    request_fingerprint: Mapped[str] = mapped_column(String(64), nullable=False)
    
    # Resolution tracking
    resolution_state: Mapped[str] = mapped_column(String(24), nullable=False, default="in_progress")
    response_status_code: Mapped[int | None] = mapped_column(Integer, nullable=True)
    returned_response_reference: Mapped[str | None] = mapped_column(String(128), nullable=True)
    replay_count: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    
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
        CheckConstraint(
            "operation_type IN ('payment_review', 'payment_submit')",
            name="ck_ir_operation_type"
        ),
        CheckConstraint(
            """resolution_state IN (
                'in_progress', 'resolved_success', 'resolved_failure', 'linked_existing_result'
            )""",
            name="ck_ir_resolution_state"
        ),
        CheckConstraint(
            "response_status_code IS NULL OR (response_status_code >= 100 AND response_status_code <= 599)",
            name="ck_ir_response_status_code"
        ),
        CheckConstraint("replay_count >= 0", name="ck_ir_replay_count"),
        UniqueConstraint(
            "customer_profile_ref_id", "operation_type", "idempotency_key",
            name="uq_idempotency_key_per_customer_operation"
        ),
    )
    
    # Relationships
    customer = relationship("CustomerProfileRef", foreign_keys=[customer_profile_ref_id])
    payment_intent = relationship("PaymentIntent", foreign_keys=[payment_intent_id])

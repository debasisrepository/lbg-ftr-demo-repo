"""
DynamicLinkApproval model (table 4.14).
Requirement: FR-PAY-007, FR-PAY-008
"""
import uuid
from datetime import UTC, datetime

from sqlalchemy import (
    BigInteger,
    CheckConstraint,
    Column,
    DateTime,
    ForeignKey,
    Index,
    Integer,
    String,
    Uuid,
)
from sqlalchemy.orm import Mapped, mapped_column

from app.database import Base


class DynamicLinkApproval(Base):
    """
    Approval bound to source account, payee, amount and reference.
    Execution requires a success row whose bound fields and fingerprint equal the intent's current values.
    """
    __tablename__ = "dynamic_link_approvals"
    
    id: Mapped[uuid.UUID] = mapped_column(Uuid, primary_key=True, default=uuid.uuid4)
    payment_intent_id: Mapped[uuid.UUID] = mapped_column(Uuid, ForeignKey("payment_intents.id"), nullable=False, index=True)
    review_version: Mapped[int] = mapped_column(Integer, nullable=False)
    review_fingerprint: Mapped[str] = mapped_column(String(64), nullable=False)
    source_account_reference: Mapped[str] = mapped_column(String(64), nullable=False)
    payee_id: Mapped[uuid.UUID] = mapped_column(Uuid, ForeignKey("payees.id"), nullable=False, index=True)
    approved_amount_minor: Mapped[int] = mapped_column(BigInteger, nullable=False)
    approved_currency: Mapped[str] = mapped_column(String(3), nullable=False)
    approved_reference_text: Mapped[str] = mapped_column(String(18), nullable=False)
    approval_challenge_reference: Mapped[str] = mapped_column(String(128), nullable=False)
    signed_approval_reference: Mapped[str | None] = mapped_column(String(256), nullable=True)
    approval_outcome: Mapped[str] = mapped_column(String(12), nullable=False, default="pending")
    approved_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    correlation_id: Mapped[str | None] = mapped_column(String(64), nullable=True, index=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, default=lambda: datetime.now(UTC))
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, default=lambda: datetime.now(UTC), onupdate=lambda: datetime.now(UTC))
    
    __table_args__ = (
        CheckConstraint("review_version >= 1", name="ck_dla_review_version"),
        CheckConstraint("approved_amount_minor > 0", name="ck_dla_amount"),
        CheckConstraint("approval_outcome IN ('pending','success','failed','abandoned','expired')", name="ck_dla_outcome"),
        CheckConstraint(
            "approval_outcome <> 'success' OR (approved_at IS NOT NULL AND signed_approval_reference IS NOT NULL)",
            name="ck_dla_success_complete"
        ),
        Index("ix_dla_payment", "payment_intent_id"),
        Index("ix_dla_payee", "payee_id"),
        Index("ix_dla_correlation", "correlation_id"),
        Index(
            "ix_dla_payment_version_success",
            "payment_intent_id",
            "review_version",
            unique=True,
            postgresql_where=Column("approval_outcome") == "success",
            sqlite_where=Column("approval_outcome") == "success"
        ),
    )

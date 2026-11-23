"""
Account read model for event-fed account overview projection.
Requirement: FR-ACCT-001, FR-ACCT-002, FR-ACCT-003
"""
import uuid
from datetime import UTC, datetime

from sqlalchemy import (
    BigInteger,
    Boolean,
    CheckConstraint,
    Column,
    DateTime,
    ForeignKey,
    Index,
    String,
    Uuid,
)
from sqlalchemy.orm import Mapped, mapped_column

from app.database import Base


class AccountReadModel(Base):
    """Event-fed projection for account overview with honest freshness."""
    __tablename__ = "account_read_models"
    
    id: Mapped[uuid.UUID] = mapped_column(Uuid, primary_key=True, default=uuid.uuid4)
    customer_profile_ref_id: Mapped[uuid.UUID] = mapped_column(Uuid, ForeignKey("customer_profile_refs.id"), nullable=False)
    account_system_reference: Mapped[str] = mapped_column(String(64), nullable=False)
    account_type: Mapped[str] = mapped_column(String(16), nullable=False)
    display_name: Mapped[str] = mapped_column(String(80), nullable=False)
    masked_account_identifier: Mapped[str] = mapped_column(String(32), nullable=False)
    balance_amount_minor = Column(BigInteger, nullable=True)
    balance_currency = Column(String(3), nullable=True)
    balance_availability_state: Mapped[str] = mapped_column(String(12), nullable=False, default="unknown")
    as_of_timestamp = Column(DateTime(timezone=True), nullable=True)
    freshness_status: Mapped[str] = mapped_column(String(14), nullable=False, default="unknown")
    freshness_breach_indicator: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    source_system_type: Mapped[str] = mapped_column(String(16), nullable=False)
    last_source_event_id = Column(String(64), nullable=True)
    last_source_event_at = Column(DateTime(timezone=True), nullable=True)
    provenance_reference: Mapped[str] = mapped_column(String(128), nullable=False)
    projection_updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, default=lambda: datetime.now(UTC))
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, default=lambda: datetime.now(UTC), onupdate=lambda: datetime.now(UTC))
    
    # Release 2: Loan-specific fields (BR-ACCT-004, BR-ACCT-007)
    loan_outstanding_balance_minor = Column(BigInteger, nullable=True)
    loan_next_repayment_date = Column(DateTime(timezone=True), nullable=True)
    loan_next_repayment_amount_minor = Column(BigInteger, nullable=True)
    loan_remaining_term_months = Column(BigInteger, nullable=True)
    
    __table_args__ = (
        CheckConstraint("account_type IN ('current','savings','card','loan')", name="ck_arm_account_type"),
        CheckConstraint("balance_availability_state IN ('current','stale','unavailable','unknown')", name="ck_arm_state"),
        CheckConstraint("freshness_status IN ('within_target','breached','unknown')", name="ck_arm_freshness"),
        CheckConstraint("source_system_type IN ('core_banking','card_platform','loan_servicing')", name="ck_arm_source"),
        CheckConstraint("balance_availability_state NOT IN ('unavailable','unknown') OR balance_amount_minor IS NULL", name="ck_arm_amount_state"),
        CheckConstraint("balance_availability_state <> 'current' OR (balance_amount_minor IS NOT NULL AND balance_currency IS NOT NULL AND as_of_timestamp IS NOT NULL)", name="ck_arm_current_needs_asof"),
        CheckConstraint("balance_amount_minor IS NULL OR balance_currency IS NOT NULL", name="ck_arm_amount_currency"),
        Index("uq_arm_customer_account", "customer_profile_ref_id", "account_system_reference", unique=True),
        Index("ix_arm_customer_freshness", "customer_profile_ref_id", "freshness_status"),
    )

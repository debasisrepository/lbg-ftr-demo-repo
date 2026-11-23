"""
Business profile read model for event-fed business account projection.
Requirement: BR-ACCT-003, BR-ACCT-010
Release 2: Business profiles and business accounts
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


class BusinessProfileReadModel(Base):
    """Event-fed projection for business account overview."""
    __tablename__ = "business_profile_read_models"
    
    id: Mapped[uuid.UUID] = mapped_column(Uuid, primary_key=True, default=uuid.uuid4)
    customer_profile_ref_id: Mapped[uuid.UUID] = mapped_column(Uuid, ForeignKey("customer_profile_refs.id"), nullable=False)
    business_name: Mapped[str] = mapped_column(String(160), nullable=False)
    business_account_system_reference: Mapped[str] = mapped_column(String(64), nullable=False)
    account_type: Mapped[str] = mapped_column(String(16), nullable=False, default="business_current")
    display_name: Mapped[str] = mapped_column(String(80), nullable=False)
    masked_account_identifier: Mapped[str] = mapped_column(String(32), nullable=False)
    balance_amount_minor = Column(BigInteger, nullable=True)
    balance_currency = Column(String(3), nullable=True)
    balance_availability_state: Mapped[str] = mapped_column(String(12), nullable=False, default="unknown")
    pending_outgoing_payments_count: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    pending_outgoing_payments_amount_minor = Column(BigInteger, nullable=True)
    as_of_timestamp = Column(DateTime(timezone=True), nullable=True)
    freshness_status: Mapped[str] = mapped_column(String(14), nullable=False, default="unknown")
    source_system_type: Mapped[str] = mapped_column(String(16), nullable=False, default="business_banking")
    projection_updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, default=lambda: datetime.now(UTC))
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, default=lambda: datetime.now(UTC), onupdate=lambda: datetime.now(UTC))
    
    __table_args__ = (
        CheckConstraint("account_type IN ('business_current','business_savings')", name="ck_bprm_account_type"),
        CheckConstraint("balance_availability_state IN ('current','stale','unavailable','unknown')", name="ck_bprm_state"),
        CheckConstraint("freshness_status IN ('within_target','breached','unknown')", name="ck_bprm_freshness"),
        Index("ix_bprm_customer", "customer_profile_ref_id"),
        Index("uq_bprm_customer_account", "customer_profile_ref_id", "business_account_system_reference", unique=True),
    )

from datetime import date, datetime

from sqlalchemy import BigInteger, Date, DateTime, ForeignKey, Index, Integer, String
from sqlalchemy.orm import Mapped, mapped_column

from app.common.enums import AccountType, FreshnessState
from app.database import Base


class AccountSnapshot(Base):
    """Account balance snapshot record."""
    __tablename__ = "account_snapshot"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    profile_id: Mapped[int] = mapped_column(Integer, ForeignKey("user_profile.id"), nullable=False)
    external_account_id: Mapped[str] = mapped_column(String(100), nullable=False)
    account_type: Mapped[str] = mapped_column(String(30), nullable=False)
    account_name: Mapped[str] = mapped_column(String(100), nullable=False)
    masked_account_number: Mapped[str] = mapped_column(String(20), nullable=False)
    sort_code: Mapped[str | None] = mapped_column(String(10), nullable=True)
    currency: Mapped[str] = mapped_column(String(3), nullable=False, default="GBP")
    current_balance_minor: Mapped[int] = mapped_column(BigInteger, nullable=False)
    available_balance_minor: Mapped[int | None] = mapped_column(BigInteger, nullable=True)
    overdraft_available_minor: Mapped[int | None] = mapped_column(BigInteger, nullable=True)
    available_credit_minor: Mapped[int | None] = mapped_column(BigInteger, nullable=True)
    freshness_state: Mapped[str] = mapped_column(String(20), nullable=False, default=FreshnessState.CURRENT.value)
    last_updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)

    __table_args__ = (
        Index("ix_account_snapshot_profile_id", "profile_id"),
        Index("ix_account_snapshot_external_id", "external_account_id"),
    )


class AccountDataGap(Base):
    """Account data gap record for observability."""
    __tablename__ = "account_data_gap"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    profile_id: Mapped[int] = mapped_column(Integer, ForeignKey("user_profile.id"), nullable=False)
    source_system: Mapped[str] = mapped_column(String(50), nullable=False)
    freshness_state: Mapped[str] = mapped_column(String(20), nullable=False)
    message: Mapped[str] = mapped_column(String(500), nullable=False)
    detected_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    cleared_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)

    __table_args__ = (
        Index("ix_account_data_gap_profile_id", "profile_id"),
    )


class LoanContextSnapshot(Base):
    """Loan context snapshot record."""
    __tablename__ = "loan_context_snapshot"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    profile_id: Mapped[int] = mapped_column(Integer, ForeignKey("user_profile.id"), nullable=False)
    account_snapshot_id: Mapped[int] = mapped_column(Integer, ForeignKey("account_snapshot.id"), nullable=False)
    next_repayment_amount_minor: Mapped[int | None] = mapped_column(BigInteger, nullable=True)
    next_repayment_due_date: Mapped[date | None] = mapped_column(Date, nullable=True)
    source_state: Mapped[str] = mapped_column(String(20), nullable=False, default=FreshnessState.CURRENT.value)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)

    __table_args__ = (
        Index("ix_loan_context_snapshot_profile_id", "profile_id"),
        Index("ix_loan_context_snapshot_account_snapshot_id", "account_snapshot_id"),
    )

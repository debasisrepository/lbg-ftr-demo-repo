from datetime import datetime

from sqlalchemy import DateTime, ForeignKey, Index, Integer, String
from sqlalchemy.orm import Mapped, mapped_column

from app.common.enums import CoPDecisionState, CoPResultCode
from app.database import Base


class Payee(Base):
    """Payee record."""
    __tablename__ = "payee"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    profile_id: Mapped[int] = mapped_column(Integer, ForeignKey("user_profile.id"), nullable=False)
    display_name: Mapped[str] = mapped_column(String(255), nullable=False)
    nickname: Mapped[str | None] = mapped_column(String(100), nullable=True)
    sort_code: Mapped[str] = mapped_column(String(10), nullable=False)
    account_number_last4: Mapped[str] = mapped_column(String(4), nullable=False)
    account_number_hash: Mapped[str] = mapped_column(String(64), nullable=False)
    can_proceed: Mapped[bool] = mapped_column(nullable=False, default=False)
    created_in_journey: Mapped[bool] = mapped_column(nullable=False, default=False)
    payee_action_sca_verified_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)

    __table_args__ = (
        Index("ix_payee_profile_id", "profile_id"),
        Index("ix_payee_account_number_hash", "account_number_hash"),
    )


class CoPResult(Base):
    """Confirmation of Payee result record."""
    __tablename__ = "cop_result"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    payee_id: Mapped[int] = mapped_column(Integer, ForeignKey("payee.id"), nullable=False)
    result_code: Mapped[str] = mapped_column(String(20), nullable=False)
    decision_state: Mapped[str] = mapped_column(String(20), nullable=False, default=CoPDecisionState.PENDING.value)
    provider_reference: Mapped[str | None] = mapped_column(String(100), nullable=True)
    returned_name: Mapped[str | None] = mapped_column(String(255), nullable=True)
    warning_message: Mapped[str | None] = mapped_column(String(500), nullable=True)
    checked_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    override_confirmed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)

    __table_args__ = (
        Index("ix_cop_result_payee_id", "payee_id"),
    )

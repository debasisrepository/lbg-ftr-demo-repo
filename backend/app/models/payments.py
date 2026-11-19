from datetime import datetime

from sqlalchemy import BigInteger, DateTime, ForeignKey, Index, Integer, String
from sqlalchemy.orm import Mapped, mapped_column

from app.common.enums import FraudDecisionCode, InstructionState, PaymentStatusCode
from app.database import Base


class PaymentInstruction(Base):
    """Payment instruction record."""
    __tablename__ = "payment_instruction"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    profile_id: Mapped[int] = mapped_column(Integer, ForeignKey("user_profile.id"), nullable=False)
    auth_session_id: Mapped[int] = mapped_column(Integer, ForeignKey("auth_session.id"), nullable=False)
    source_account_snapshot_id: Mapped[int] = mapped_column(Integer, ForeignKey("account_snapshot.id"), nullable=False)
    payee_id: Mapped[int] = mapped_column(Integer, ForeignKey("payee.id"), nullable=False)
    amount_minor: Mapped[int] = mapped_column(BigInteger, nullable=False)
    currency: Mapped[str] = mapped_column(String(3), nullable=False, default="GBP")
    reference_text: Mapped[str | None] = mapped_column(String(255), nullable=True)
    client_idempotency_key: Mapped[str] = mapped_column(String(100), unique=True, nullable=False)
    payment_reference: Mapped[str | None] = mapped_column(String(100), nullable=True)
    instruction_state: Mapped[str] = mapped_column(String(20), nullable=False, default=InstructionState.PREPARED.value)
    duplicate_submission_blocked: Mapped[bool] = mapped_column(nullable=False, default=False)
    expected_arrival_message: Mapped[str | None] = mapped_column(String(500), nullable=True)
    failure_reason: Mapped[str | None] = mapped_column(String(500), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)

    __table_args__ = (
        Index("ix_payment_instruction_profile_id", "profile_id"),
        Index("ix_payment_instruction_auth_session_id", "auth_session_id"),
        Index("ix_payment_instruction_source_account_snapshot_id", "source_account_snapshot_id"),
        Index("ix_payment_instruction_payee_id", "payee_id"),
        Index("ix_payment_instruction_client_idempotency_key", "client_idempotency_key"),
        Index("ix_payment_instruction_state", "instruction_state"),
    )


class FraudDecision(Base):
    """Fraud decision record."""
    __tablename__ = "fraud_decision"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    payment_instruction_id: Mapped[int] = mapped_column(Integer, ForeignKey("payment_instruction.id"), nullable=False)
    decision_code: Mapped[str] = mapped_column(String(20), nullable=False)
    warning_message: Mapped[str | None] = mapped_column(String(500), nullable=True)
    hold_reason: Mapped[str | None] = mapped_column(String(500), nullable=True)
    provider_reference: Mapped[str | None] = mapped_column(String(100), nullable=True)
    decided_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)

    __table_args__ = (
        Index("ix_fraud_decision_payment_instruction_id", "payment_instruction_id"),
    )


class PaymentApproval(Base):
    """Payment approval record."""
    __tablename__ = "payment_approval"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    payment_instruction_id: Mapped[int] = mapped_column(Integer, ForeignKey("payment_instruction.id"), nullable=False)
    challenge_id: Mapped[int | None] = mapped_column(Integer, ForeignKey("step_up_challenge.id"), nullable=True)
    sca_method: Mapped[str] = mapped_column(String(20), nullable=False)
    dynamic_link_hash: Mapped[str | None] = mapped_column(String(64), nullable=True)
    approved_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)

    __table_args__ = (
        Index("ix_payment_approval_payment_instruction_id", "payment_instruction_id"),
        Index("ix_payment_approval_challenge_id", "challenge_id"),
    )


class PaymentStatusHistory(Base):
    """Payment status history record."""
    __tablename__ = "payment_status_history"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    payment_instruction_id: Mapped[int] = mapped_column(Integer, ForeignKey("payment_instruction.id"), nullable=False)
    status_code: Mapped[str] = mapped_column(String(20), nullable=False)
    rail_reference: Mapped[str | None] = mapped_column(String(100), nullable=True)
    reason_code: Mapped[str | None] = mapped_column(String(50), nullable=True)
    reason_detail: Mapped[str | None] = mapped_column(String(500), nullable=True)
    effective_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)

    __table_args__ = (
        Index("ix_payment_status_history_payment_instruction_id", "payment_instruction_id"),
        Index("ix_payment_status_history_status_code", "status_code"),
    )

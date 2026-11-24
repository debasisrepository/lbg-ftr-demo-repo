"""Promise-to-pay models."""
import uuid
from datetime import datetime
from decimal import Decimal

from sqlalchemy import CheckConstraint, DateTime, ForeignKey, Index, Numeric, String, Uuid
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.db import Base


class PromiseToPay(Base):
    """Promise to pay record."""

    __tablename__ = "promises_to_pay"

    id: Mapped[uuid.UUID] = mapped_column(Uuid, primary_key=True, default=uuid.uuid4)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)

    customer_account_id: Mapped[uuid.UUID] = mapped_column(Uuid, ForeignKey("customer_accounts.id"), nullable=False, index=True)
    source_interaction_log_entry_id: Mapped[uuid.UUID | None] = mapped_column(
        Uuid, ForeignKey("interaction_log_entries.id"), nullable=True, index=True
    )
    promised_amount: Mapped[Decimal] = mapped_column(Numeric(18, 2), nullable=False)
    currency_code: Mapped[str] = mapped_column(String(3), nullable=False)
    promised_date: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, index=True)
    promise_scope_type: Mapped[str] = mapped_column(String(50), nullable=False)
    promise_status: Mapped[str] = mapped_column(String(50), nullable=False, index=True)
    captured_by_user_id: Mapped[uuid.UUID] = mapped_column(Uuid, ForeignKey("users.id"), nullable=False, index=True)
    captured_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, index=True)
    breach_detected_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    policy_evaluation_record_id: Mapped[uuid.UUID | None] = mapped_column(
        Uuid, ForeignKey("policy_evaluation_records.id"), nullable=True, index=True
    )
    idempotency_key: Mapped[str] = mapped_column(String(255), nullable=False)

    # Relationships
    scope_links: Mapped[list["PromiseScopeLink"]] = relationship(
        "PromiseScopeLink", back_populates="promise", lazy="select"
    )

    __table_args__ = (
        CheckConstraint("promise_scope_type IN ('full_account', 'invoice_specific', 'partial_amount')", name="ck_promises_to_pay_scope_type"),
        CheckConstraint("promise_status IN ('captured', 'kept', 'breached', 'waived')", name="ck_promises_to_pay_status"),
        Index("uq_promises_user_idempotency", "captured_by_user_id", "idempotency_key", unique=True),
        Index("ix_promises_to_pay_account_status", "customer_account_id", "promise_status"),
    )


class PromiseScopeLink(Base):
    """Link between promise and invoice/receivable item."""

    __tablename__ = "promise_scope_links"

    id: Mapped[uuid.UUID] = mapped_column(Uuid, primary_key=True, default=uuid.uuid4)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)

    promise_to_pay_id: Mapped[uuid.UUID] = mapped_column(Uuid, ForeignKey("promises_to_pay.id"), nullable=False, index=True)
    link_type: Mapped[str] = mapped_column(String(50), nullable=False)
    invoice_id: Mapped[uuid.UUID | None] = mapped_column(Uuid, ForeignKey("invoices.id"), nullable=True, index=True)
    receivable_item_id: Mapped[uuid.UUID | None] = mapped_column(Uuid, ForeignKey("receivable_items.id"), nullable=True, index=True)
    linked_amount: Mapped[Decimal | None] = mapped_column(Numeric(18, 2), nullable=True)

    # Relationships
    promise: Mapped["PromiseToPay"] = relationship("PromiseToPay", back_populates="scope_links")

    __table_args__ = (
        CheckConstraint("link_type IN ('invoice', 'receivable_item')", name="ck_promise_scope_links_type"),
    )


class IdempotencyRecord(Base):
    """Idempotency record for mutating operations."""

    __tablename__ = "idempotency_records"

    id: Mapped[uuid.UUID] = mapped_column(Uuid, primary_key=True, default=uuid.uuid4)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)

    user_id: Mapped[uuid.UUID] = mapped_column(Uuid, ForeignKey("users.id"), nullable=False, index=True)
    operation: Mapped[str] = mapped_column(String(50), nullable=False)
    idempotency_key: Mapped[str] = mapped_column(String(255), nullable=False)
    request_fingerprint: Mapped[str] = mapped_column(String(64), nullable=False)
    response_status_code: Mapped[int] = mapped_column(nullable=False)
    response_body_json: Mapped[str | None] = mapped_column(String(10000), nullable=True)
    resource_type: Mapped[str | None] = mapped_column(String(50), nullable=True)
    resource_id: Mapped[uuid.UUID | None] = mapped_column(Uuid, nullable=True)
    expires_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, index=True)

    __table_args__ = (
        Index("uq_idempotency_records_user_op_key", "user_id", "operation", "idempotency_key", unique=True),
    )

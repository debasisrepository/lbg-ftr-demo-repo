"""Receivable items and SAP sync models."""
import uuid
from datetime import datetime
from decimal import Decimal

from sqlalchemy import (
    Boolean,
    CheckConstraint,
    DateTime,
    ForeignKey,
    Index,
    Integer,
    Numeric,
    String,
    Uuid,
)
from sqlalchemy.orm import Mapped, mapped_column

from app.core.db import Base


class ReceivableItem(Base):
    """Receivable open item from SAP."""

    __tablename__ = "receivable_items"

    id: Mapped[uuid.UUID] = mapped_column(Uuid, primary_key=True, default=uuid.uuid4)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)

    invoice_id: Mapped[uuid.UUID | None] = mapped_column(Uuid, ForeignKey("invoices.id"), nullable=True, index=True)
    customer_account_id: Mapped[uuid.UUID] = mapped_column(Uuid, ForeignKey("customer_accounts.id"), nullable=False, index=True)
    sap_open_item_ref: Mapped[str] = mapped_column(String(50), nullable=False, unique=True, index=True)
    aging_bucket: Mapped[str | None] = mapped_column(String(50), nullable=True, index=True)
    days_past_due: Mapped[int | None] = mapped_column(Integer, nullable=True, index=True)
    open_amount: Mapped[Decimal] = mapped_column(Numeric(18, 2), nullable=False, index=True)
    currency_code: Mapped[str] = mapped_column(String(3), nullable=False)
    dispute_indicator: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False, index=True)
    deduction_indicator: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    unapplied_cash_indicator: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False, index=True)
    pending_evidence_indicator: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False, index=True)
    promise_indicator: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False, index=True)
    current_collectibility_status: Mapped[str | None] = mapped_column(String(50), nullable=True)
    last_sync_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)

    __table_args__ = (
        Index("ix_receivable_items_account_flags", "customer_account_id", "dispute_indicator", "unapplied_cash_indicator"),
    )


class UnappliedCashReference(Base):
    """Unapplied cash from SAP."""

    __tablename__ = "unapplied_cash_references"

    id: Mapped[uuid.UUID] = mapped_column(Uuid, primary_key=True, default=uuid.uuid4)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)

    customer_account_id: Mapped[uuid.UUID] = mapped_column(Uuid, ForeignKey("customer_accounts.id"), nullable=False, index=True)
    sap_cash_item_ref: Mapped[str] = mapped_column(String(50), nullable=False, unique=True, index=True)
    bank_or_lockbox_reference: Mapped[str | None] = mapped_column(String(100), nullable=True)
    receipt_date: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True, index=True)
    unapplied_amount: Mapped[Decimal] = mapped_column(Numeric(18, 2), nullable=False)
    currency_code: Mapped[str] = mapped_column(String(3), nullable=False)
    classification_status: Mapped[str | None] = mapped_column(String(50), nullable=True)
    aging_days: Mapped[int | None] = mapped_column(Integer, nullable=True)
    resolution_status: Mapped[str | None] = mapped_column(String(50), nullable=True)
    last_sync_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)


class SapTransactionReference(Base):
    """SAP transaction reference for financial confirmation."""

    __tablename__ = "sap_transaction_references"

    id: Mapped[uuid.UUID] = mapped_column(Uuid, primary_key=True, default=uuid.uuid4)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)

    invoice_id: Mapped[uuid.UUID | None] = mapped_column(Uuid, ForeignKey("invoices.id"), nullable=True, index=True)
    receivable_item_id: Mapped[uuid.UUID | None] = mapped_column(Uuid, ForeignKey("receivable_items.id"), nullable=True, index=True)
    reference_type: Mapped[str] = mapped_column(String(50), nullable=False, index=True)
    sap_object_id: Mapped[str] = mapped_column(String(50), nullable=False)
    sap_object_subtype: Mapped[str | None] = mapped_column(String(50), nullable=True)
    company_code: Mapped[str] = mapped_column(String(10), nullable=False)
    document_number: Mapped[str] = mapped_column(String(50), nullable=False)
    fiscal_year: Mapped[str] = mapped_column(String(4), nullable=False)
    line_item_number: Mapped[str | None] = mapped_column(String(10), nullable=True)
    status_snapshot: Mapped[str | None] = mapped_column(String(100), nullable=True)
    snapshot_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    is_final_financial_confirmation: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)

    __table_args__ = (
        Index(
            "uq_sap_transaction_ref",
            "company_code",
            "document_number",
            "fiscal_year",
            "line_item_number",
            "reference_type",
            unique=True
        ),
    )


class SapSyncRun(Base):
    """SAP synchronization run record."""

    __tablename__ = "sap_sync_runs"

    id: Mapped[uuid.UUID] = mapped_column(Uuid, primary_key=True, default=uuid.uuid4)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)

    sync_scope: Mapped[str] = mapped_column(String(100), nullable=False, index=True)
    trigger_type: Mapped[str] = mapped_column(String(50), nullable=False)
    triggered_by_user_id: Mapped[uuid.UUID | None] = mapped_column(Uuid, ForeignKey("users.id"), nullable=True, index=True)
    started_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, index=True)
    completed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    run_status: Mapped[str] = mapped_column(String(50), nullable=False, index=True)
    records_read: Mapped[int | None] = mapped_column(Integer, nullable=True)
    records_upserted: Mapped[int | None] = mapped_column(Integer, nullable=True)
    error_summary: Mapped[str | None] = mapped_column(String(1000), nullable=True)
    correlation_id: Mapped[str | None] = mapped_column(String(36), nullable=True, index=True)

    __table_args__ = (
        CheckConstraint("run_status IN ('running', 'succeeded', 'failed', 'partial')", name="ck_sap_sync_runs_status"),
        CheckConstraint("trigger_type IN ('scheduled', 'user_refresh', 'manual')", name="ck_sap_sync_runs_trigger"),
    )

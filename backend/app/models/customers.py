"""Customer and account models from SAP reference data."""
import uuid
from datetime import datetime
from decimal import Decimal

from sqlalchemy import DateTime, ForeignKey, Index, Numeric, String, Uuid
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.db import Base


class Customer(Base):
    """Customer master from SAP."""

    __tablename__ = "customers"

    id: Mapped[uuid.UUID] = mapped_column(Uuid, primary_key=True, default=uuid.uuid4)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)

    sap_customer_ref: Mapped[str] = mapped_column(String(50), nullable=False, unique=True, index=True)
    customer_name: Mapped[str] = mapped_column(String(255), nullable=False)
    regional_business_unit: Mapped[str | None] = mapped_column(String(50), nullable=True, index=True)
    credit_status_indicator: Mapped[str | None] = mapped_column(String(50), nullable=True)
    master_data_source: Mapped[str | None] = mapped_column(String(50), nullable=True)
    last_sync_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True, index=True)


class CustomerAccount(Base):
    """Customer account from SAP."""

    __tablename__ = "customer_accounts"

    id: Mapped[uuid.UUID] = mapped_column(Uuid, primary_key=True, default=uuid.uuid4)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)

    customer_id: Mapped[uuid.UUID] = mapped_column(Uuid, ForeignKey("customers.id"), nullable=False, index=True)
    sap_account_ref: Mapped[str] = mapped_column(String(50), nullable=False)
    company_code: Mapped[str] = mapped_column(String(10), nullable=False, index=True)
    currency_code: Mapped[str] = mapped_column(String(3), nullable=False, default="USD")
    account_status: Mapped[str | None] = mapped_column(String(50), nullable=True)
    risk_segment: Mapped[str | None] = mapped_column(String(50), nullable=True, index=True)
    portfolio_ref: Mapped[str | None] = mapped_column(String(50), nullable=True, index=True)
    collector_owner_user_id: Mapped[uuid.UUID | None] = mapped_column(Uuid, ForeignKey("users.id"), nullable=True, index=True)
    last_sync_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)

    # Relationships
    customer: Mapped["Customer"] = relationship("Customer", lazy="joined")

    __table_args__ = (
        Index("uq_customer_accounts_company_sap_account", "company_code", "sap_account_ref", unique=True),
    )


class Invoice(Base):
    """Invoice from SAP."""

    __tablename__ = "invoices"

    id: Mapped[uuid.UUID] = mapped_column(Uuid, primary_key=True, default=uuid.uuid4)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)

    customer_account_id: Mapped[uuid.UUID] = mapped_column(Uuid, ForeignKey("customer_accounts.id"), nullable=False, index=True)
    sap_invoice_ref: Mapped[str] = mapped_column(String(50), nullable=False, unique=True, index=True)
    invoice_number: Mapped[str] = mapped_column(String(50), nullable=False, index=True)
    document_date: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    due_date: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, index=True)
    invoice_amount: Mapped[Decimal] = mapped_column(Numeric(18, 2), nullable=False)
    open_amount: Mapped[Decimal] = mapped_column(Numeric(18, 2), nullable=False, index=True)
    currency_code: Mapped[str] = mapped_column(String(3), nullable=False)
    invoice_status: Mapped[str | None] = mapped_column(String(50), nullable=True, index=True)
    billing_channel_type: Mapped[str | None] = mapped_column(String(50), nullable=True)
    billing_evidence_status: Mapped[str | None] = mapped_column(String(50), nullable=True)
    last_sync_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)

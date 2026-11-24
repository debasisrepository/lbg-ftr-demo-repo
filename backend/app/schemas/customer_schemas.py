"""Pydantic schemas for customer endpoints."""
from datetime import datetime
from typing import Any, Dict, List, Literal, Optional
from pydantic import BaseModel, Field


# Common types
class Section(BaseModel):
    """Section wrapper for Customer360."""
    status: Literal["available", "unavailable", "masked"]
    reason: Optional[str] = None
    as_of: Optional[datetime] = None
    data: Optional[Any] = None


# Customer list
class CustomerListItem(BaseModel):
    """Customer list item."""
    customer_id: str
    customer_name: str
    sap_customer_ref: str
    regional_business_unit: Optional[str] = None
    credit_status_indicator: Optional[str] = None
    account_count: int


class CustomerListResponse(BaseModel):
    """Customer list response."""
    items: List[CustomerListItem]
    total: int
    limit: int
    offset: int


# Customer 360
class ProfileData(BaseModel):
    """Customer profile data."""
    customer_id: str
    customer_name: str
    sap_customer_ref: str
    regional_business_unit: Optional[str] = None
    credit_status_indicator: Optional[str] = None  # May be masked
    master_data_source: Optional[str] = None


class AccountData(BaseModel):
    """Customer account data."""
    customer_account_id: str
    sap_account_ref: str
    company_code: str
    currency_code: str
    account_status: str
    risk_segment: Optional[str] = None
    portfolio_ref: Optional[str] = None
    collector_owner_user_id: Optional[str] = None
    open_balance: str  # Decimal as string


class InvoiceData(BaseModel):
    """Invoice data."""
    invoice_id: str
    sap_invoice_ref: str
    invoice_number: str
    document_date: datetime
    due_date: datetime
    invoice_amount: str  # Decimal as string
    open_amount: str
    currency_code: str
    invoice_status: str


class ReceivableItemData(BaseModel):
    """Receivable item data."""
    receivable_item_id: str
    sap_open_item_ref: str
    aging_bucket: str
    days_past_due: int
    open_amount: str
    currency_code: str
    dispute_indicator: bool
    deduction_indicator: bool
    promise_indicator: bool


class UnappliedCashData(BaseModel):
    """Unapplied cash data."""
    unapplied_cash_id: str
    sap_cash_item_ref: str
    bank_or_lockbox_reference: Optional[str] = None
    receipt_date: datetime
    unapplied_amount: str
    currency_code: str
    classification_status: str
    aging_days: int


class PromiseData(BaseModel):
    """Promise data."""
    promise_id: str
    promised_amount: str
    currency_code: str
    promised_date: datetime
    promise_scope_type: str
    promise_status: str
    captured_by_user_id: str
    captured_at: datetime


class InteractionData(BaseModel):
    """Interaction data."""
    interaction_id: str
    interaction_type: str
    interaction_direction: str
    interaction_channel: str
    occurred_at: datetime
    recorded_by_user_id: str
    summary_text: Optional[str] = None


class Customer360Response(BaseModel):
    """Customer 360 response with sections."""
    customer_id: str
    generated_at: datetime
    data_freshness: datetime
    profile: Section
    accounts: Section
    invoices: Section
    receivable_items: Section
    unapplied_cash: Section
    promises: Section
    source_interactions: Section

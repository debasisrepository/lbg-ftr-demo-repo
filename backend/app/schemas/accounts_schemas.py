"""
Account overview schemas.
Requirement: FR-ACCT-001, FR-ACCT-002, FR-ACCT-003
Release 2: BR-ACCT-002, BR-ACCT-003, BR-ACCT-004 (loans, business profiles)
"""
from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field


class Balance(BaseModel):
    """Balance with availability state."""
    availability_state: str = Field(..., description="current, stale, unavailable, unknown")
    amount_minor: int | None = Field(None, description="Amount in minor units, null when unavailable")
    currency: str | None = Field(None, max_length=3, description="ISO 4217 currency code")
    display_text: str = Field(..., description="Plain-language balance text")


class LoanDetails(BaseModel):
    """Loan-specific details (Release 2: BR-ACCT-004)."""
    outstanding_balance_minor: int | None = Field(None, description="Outstanding loan balance in minor units")
    next_repayment_date: datetime | None = Field(None, description="Next scheduled repayment date")
    next_repayment_amount_minor: int | None = Field(None, description="Next repayment amount in minor units")
    remaining_term_months: int | None = Field(None, description="Remaining loan term in months")
    
    model_config = ConfigDict(from_attributes=True)


class AccountItem(BaseModel):
    """Account item in overview response."""
    account_id: str = Field(..., description="UUID of account read model")
    account_type: str = Field(..., description="current, savings, card, loan")
    display_name: str = Field(..., max_length=80, description="Customer-facing account name")
    masked_account_identifier: str = Field(..., max_length=32, description="Masked account number")
    balance: Balance
    as_of_timestamp: datetime | None = Field(None, description="Source time of balance, null means not current")
    freshness_status: str = Field(..., description="within_target, breached, unknown")
    freshness_text: str = Field(..., description="Accessible plain-language freshness indicator")
    item_state: str = Field(..., description="available or partial")
    payment_source_eligible: bool = Field(..., description="True if account can be used as payment source")
    loan_details: LoanDetails | None = Field(None, description="Loan-specific details (Release 2)")
    
    model_config = ConfigDict(from_attributes=True)


class CapabilityStatus(BaseModel):
    """Capability status for degraded mode handling."""
    capability_name: str = Field(..., description="accounts_overview, saved_payees, payments, payment_status")
    status_value: str = Field(..., description="healthy, stale, partial, unavailable, restricted")
    customer_message_code: str | None = Field(None, description="Message catalog key")
    customer_message: str = Field(..., description="Plain-language status message")
    recovery_guidance: str | None = Field(None, description="Plain-language recovery guidance")
    effective_from: datetime = Field(..., description="When this state became effective")
    
    model_config = ConfigDict(from_attributes=True)


class AccountOverviewResponse(BaseModel):
    """
    Account overview response with pagination and capability state.
    E-04 GET /api/v1/accounts
    """
    items: list[AccountItem] = Field(..., description="Accounts on this page")
    total: int = Field(..., description="Total accounts for customer")
    page: int = Field(..., description="Current page (1-based)")
    page_size: int = Field(..., description="Items per page")
    overview_state: str = Field(..., description="complete, partial, or unavailable")
    capability: CapabilityStatus = Field(..., description="accounts_overview capability status")
    
    model_config = ConfigDict(from_attributes=True)

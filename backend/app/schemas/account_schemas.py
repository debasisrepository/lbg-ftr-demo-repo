"""Account and loan API schemas"""
import uuid
from datetime import date, datetime
from typing import Optional

from pydantic import BaseModel, Field


class BankAccountOut(BaseModel):
    """Bank account response"""
    bank_account_id: uuid.UUID
    external_account_ref: Optional[str] = None
    account_type: str
    account_name: str
    sort_code_masked: Optional[str] = None
    account_number_masked: Optional[str] = None
    currency_code: str
    account_holder_name: Optional[str] = None
    current_balance_minor: Optional[int] = Field(None, description="Balance in pence (None if unavailable)")
    available_balance_minor: Optional[int] = Field(None, description="Available balance in pence")
    overdraft_limit_minor: Optional[int] = Field(None, description="Overdraft limit in pence")
    freshness_at: Optional[datetime] = Field(None, description="Last updated timestamp")
    source_status: str = Field(description="fresh, stale, or unavailable")
    payment_permission: bool = Field(False, description="Whether profile can pay from this account")

    class Config:
        from_attributes = True


class LoanSnapshotOut(BaseModel):
    """Loan snapshot response"""
    loan_snapshot_id: uuid.UUID
    profile_id: uuid.UUID
    external_loan_ref: Optional[str] = None
    loan_name: str
    outstanding_balance_minor: Optional[int] = Field(None, description="Outstanding balance in pence")
    next_repayment_minor: Optional[int] = Field(None, description="Next repayment amount in pence")
    next_repayment_date: Optional[date] = None
    currency_code: str
    freshness_at: Optional[datetime] = None
    source_status: str = Field(description="fresh, stale, or unavailable")

    class Config:
        from_attributes = True


class AccountsOverviewResponse(BaseModel):
    """Accounts overview response"""
    accounts: list[BankAccountOut]
    loans: list[LoanSnapshotOut]
    profile_id: uuid.UUID
    profile_display_name: str

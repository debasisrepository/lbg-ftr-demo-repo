"""Account domain schemas."""
from datetime import date, datetime
from pydantic import BaseModel, Field


class AccountInfo(BaseModel):
    """Account information in overview."""
    account_id: int = Field(..., description="Internal account snapshot ID")
    account_type: str = Field(..., description="Account type")
    account_name: str = Field(..., description="Account name")
    masked_account_number: str = Field(..., description="Masked account number")
    sort_code: str | None = Field(None, description="Sort code")
    currency: str = Field(..., description="Currency code")
    current_balance_minor: int = Field(..., description="Current balance in minor units")
    available_balance_minor: int | None = Field(None, description="Available balance in minor units")
    overdraft_available_minor: int | None = Field(None, description="Overdraft available in minor units")
    available_credit_minor: int | None = Field(None, description="Available credit in minor units")
    next_repayment_amount_minor: int | None = Field(None, description="Next repayment amount in minor units")
    next_repayment_due_date: date | None = Field(None, description="Next repayment due date")
    freshness_state: str = Field(..., description="Data freshness state")
    last_updated_at: datetime = Field(..., description="Last updated timestamp")


class DataGapInfo(BaseModel):
    """Data gap information."""
    source_system: str = Field(..., description="Source system name")
    message: str = Field(..., description="Gap message")
    freshness_state: str = Field(..., description="Freshness state")


class ProfileContext(BaseModel):
    """Profile context in overview."""
    profile_id: int = Field(..., description="Profile ID")
    profile_type: str = Field(..., description="Profile type")
    display_name: str = Field(..., description="Display name")
    business_name: str | None = Field(None, description="Business name if applicable")


class AccountOverviewResponse(BaseModel):
    """Response for GET /accounts/overview."""
    profile: ProfileContext = Field(..., description="Active profile context")
    accounts: list[AccountInfo] = Field(..., description="Account list")
    data_gaps: list[DataGapInfo] = Field(..., description="Data gaps if any")

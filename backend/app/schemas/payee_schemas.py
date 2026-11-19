"""Payee domain schemas."""
from datetime import datetime
from pydantic import BaseModel, Field


class PayeeInfo(BaseModel):
    """Payee information in list."""
    payee_id: int = Field(..., description="Payee ID")
    display_name: str = Field(..., description="Payee display name")
    sort_code: str = Field(..., description="Sort code")
    masked_account_number: str = Field(..., description="Masked account number (last 4 digits)")
    nickname: str | None = Field(None, description="Nickname")
    can_proceed: bool = Field(..., description="Whether can proceed to payment")
    latest_cop_result: str | None = Field(None, description="Latest CoP result code")
    latest_cop_checked_at: datetime | None = Field(None, description="Latest CoP check timestamp")


class PayeeListResponse(BaseModel):
    """Response for GET /payees."""
    payees: list[PayeeInfo] = Field(..., description="Payee list")


class CreatePayeeRequest(BaseModel):
    """Request to create a new payee."""
    profile_id: int = Field(..., description="Profile ID")
    display_name: str = Field(..., description="Payee display name", max_length=140)
    nickname: str | None = Field(None, description="Nickname", max_length=140)
    sort_code: str = Field(..., description="Sort code", pattern=r"^\d{2}-\d{2}-\d{2}$")
    account_number: str = Field(..., description="Full account number", pattern=r"^\d{8}$")
    payee_action_challenge_id: int = Field(..., description="Challenge ID for payee action SCA")
    payee_action_assertion: str = Field(..., description="SCA assertion (passcode or biometric)")


class CoPOverrideRequest(BaseModel):
    """Request to confirm CoP warning."""
    override_reason: str = Field(..., description="Reason for override", max_length=500)


class PayeeResponse(BaseModel):
    """Response for POST /payees."""
    payee_id: int = Field(..., description="Created payee ID")
    display_name: str = Field(..., description="Payee display name")
    sort_code: str = Field(..., description="Sort code")
    masked_account_number: str = Field(..., description="Masked account number")
    cop_result: str = Field(..., description="CoP result code")
    warning_message: str | None = Field(None, description="Warning message if any")
    can_proceed: bool = Field(..., description="Whether can proceed")
    override_required: bool = Field(..., description="Whether override is required")

"""Payee and CoP API schemas"""
import uuid
from datetime import datetime
from typing import Optional

from pydantic import BaseModel, Field, field_validator


class CopCheckOut(BaseModel):
    """CoP check response"""
    cop_check_id: uuid.UUID
    outcome: str = Field(description="match, partial_match, mismatch, or unavailable")
    suggested_name: Optional[str] = None
    policy_treatment: str = Field(description="allow, warn, or block")
    checked_at: datetime
    expires_at: Optional[datetime] = None
    customer_acknowledged_at: Optional[datetime] = None

    class Config:
        from_attributes = True


class PayeeOut(BaseModel):
    """Payee response"""
    payee_id: uuid.UUID
    customer_id: uuid.UUID
    profile_id: Optional[uuid.UUID] = None
    payee_name: str
    sort_code: str
    account_number_masked: str
    payee_type: str = Field(description="personal or business")
    is_saved: bool
    status: str = Field(description="active, pending_verification, or inactive")
    last_verified_at: Optional[datetime] = None
    latest_cop_check: Optional[CopCheckOut] = None

    class Config:
        from_attributes = True


class PayeeListResponse(BaseModel):
    """List of payees"""
    payees: list[PayeeOut]


class CreatePayeeRequest(BaseModel):
    """Create payee request"""
    payee_name: str = Field(min_length=2, max_length=140)
    sort_code: str = Field(pattern=r"^\d{2}-\d{2}-\d{2}$")
    account_number: str = Field(min_length=8, max_length=8, pattern=r"^\d{8}$")
    payee_type: str = Field(pattern=r"^(personal|business)$")

    @field_validator('payee_name')
    @classmethod
    def validate_payee_name(cls, v: str) -> str:
        if len(v.strip()) < 2:
            raise ValueError("Payee name must be at least 2 characters")
        return v.strip()


class CreatePayeeResponse(BaseModel):
    """Create payee response"""
    payee: PayeeOut
    cop_check: CopCheckOut


class UpdatePayeeRequest(BaseModel):
    """Update payee request"""
    payee_name: Optional[str] = Field(None, min_length=2, max_length=140)
    sort_code: Optional[str] = Field(None, pattern=r"^\d{2}-\d{2}-\d{2}$")
    account_number: Optional[str] = Field(None, min_length=8, max_length=8, pattern=r"^\d{8}$")

    @field_validator('payee_name')
    @classmethod
    def validate_payee_name(cls, v: Optional[str]) -> Optional[str]:
        if v is not None and len(v.strip()) < 2:
            raise ValueError("Payee name must be at least 2 characters")
        return v.strip() if v else None


class UpdatePayeeResponse(BaseModel):
    """Update payee response"""
    payee: PayeeOut
    cop_check: Optional[CopCheckOut] = None


class AcknowledgeCopRequest(BaseModel):
    """Acknowledge CoP mismatch request"""
    acknowledged: bool = Field(True)


class AcknowledgeCopResponse(BaseModel):
    """Acknowledge CoP mismatch response"""
    payee_id: uuid.UUID
    acknowledged_at: datetime
    message: str = "CoP acknowledgement recorded"


class RunCopCheckRequest(BaseModel):
    """Manually run CoP check request"""
    reason: str = Field(default="recheck")


class RunCopCheckResponse(BaseModel):
    """CoP check response"""
    cop_check: CopCheckOut

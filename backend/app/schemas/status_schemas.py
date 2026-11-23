"""
Capability status schemas.
Requirement: FR-ACCT-001, FR-ACCT-003, FR-PAY-001, FR-PAY-011
"""
from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field


class CapabilityStatusItem(BaseModel):
    """Individual capability status."""
    capability_name: str = Field(..., description="accounts_overview, saved_payees, payments, payment_status")
    status_value: str = Field(..., description="healthy, stale, partial, unavailable, restricted")
    customer_message_code: str | None = Field(None, description="Message catalog key")
    customer_message: str = Field(..., description="Plain-language status message")
    recovery_guidance: str | None = Field(None, description="Plain-language recovery guidance")
    effective_from: datetime = Field(..., description="When this state became effective")
    
    model_config = ConfigDict(from_attributes=True)


class CapabilityStatusListResponse(BaseModel):
    """
    Capability status list response.
    E-06 GET /api/v1/capability-statuses
    """
    items: list[CapabilityStatusItem] = Field(..., description="One entry per capability")
    total: int = Field(..., description="Number of capabilities (always 4)")
    page: int = Field(default=1, description="Always 1")
    page_size: int = Field(..., description="Number of items on page")
    
    model_config = ConfigDict(from_attributes=True)

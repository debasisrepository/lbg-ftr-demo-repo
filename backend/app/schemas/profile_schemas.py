"""Profile and entitlement API schemas"""
import uuid
from datetime import datetime
from typing import Optional

from pydantic import BaseModel, Field


class EntitlementOut(BaseModel):
    """Entitlement response"""
    entitlement_id: uuid.UUID
    profile_id: uuid.UUID
    entitlement_code: str
    capability_type: str
    can_view_accounts: bool
    can_manage_payees: bool
    can_initiate_payments: bool
    effective_from: Optional[datetime] = None
    effective_to: Optional[datetime] = None

    class Config:
        from_attributes = True


class ProfileOut(BaseModel):
    """Profile response"""
    profile_id: uuid.UUID
    customer_id: uuid.UUID
    profile_type: str
    display_name: str
    status: str
    entitlements: list[EntitlementOut] = []

    class Config:
        from_attributes = True


class ProfileListResponse(BaseModel):
    """List of customer profiles"""
    profiles: list[ProfileOut]


class SetActiveProfileRequest(BaseModel):
    """Request to set active profile"""
    profile_id: uuid.UUID = Field(description="Profile to activate")


class SetActiveProfileResponse(BaseModel):
    """Response for set active profile"""
    profile_id: uuid.UUID
    display_name: str
    message: str = "Active profile updated"

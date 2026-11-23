"""
Profile management schemas.
Requirement: BR-ACCT-002, BR-ACCT-003, BR-ACCT-010
Release 2: Profile switching and business profiles
"""
from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field


class ProfileSummary(BaseModel):
    """Summary of a customer profile (personal or business)."""
    profile_id: str = Field(..., description="UUID of customer profile reference")
    profile_type: str = Field(..., description="personal or business")
    display_name: str = Field(..., max_length=120, description="Profile display name")
    business_name: str | None = Field(None, max_length=160, description="Business name for business profiles")
    is_active: bool = Field(..., description="Whether profile is active")
    has_view_entitlement: bool = Field(..., description="Whether user has view permission on this profile")
    has_pay_entitlement: bool = Field(..., description="Whether user has pay permission on this profile")
    
    model_config = ConfigDict(from_attributes=True)


class ProfilesResponse(BaseModel):
    """
    Response for GET /api/v1/profiles - all profiles for authenticated identity.
    Per ADR-003: One identity, many profiles.
    Per BRL-ACCT-03: Show profile only if user has at least one active entitlement.
    """
    profiles: list[ProfileSummary] = Field(..., description="Profiles with at least one active entitlement")
    active_profile_id: str = Field(..., description="Currently active profile ID")
    
    model_config = ConfigDict(from_attributes=True)


class SwitchProfileRequest(BaseModel):
    """Request to switch active profile."""
    profile_id: str = Field(..., description="UUID of profile to switch to")


class SwitchProfileResponse(BaseModel):
    """Response after profile switch."""
    active_profile_id: str = Field(..., description="New active profile ID")
    profile_type: str = Field(..., description="personal or business")
    display_name: str = Field(..., max_length=120, description="Profile display name")
    business_name: str | None = Field(None, max_length=160, description="Business name for business profiles")
    
    model_config = ConfigDict(from_attributes=True)


class BusinessAccountItem(BaseModel):
    """Business account item with pending payments info."""
    account_id: str = Field(..., description="UUID of business account read model")
    account_type: str = Field(..., description="business_current or business_savings")
    business_name: str = Field(..., max_length=160, description="Business name")
    display_name: str = Field(..., max_length=80, description="Account display name")
    masked_account_identifier: str = Field(..., max_length=32, description="Masked account number")
    available_balance_minor: int | None = Field(None, description="Available balance in minor units")
    currency: str | None = Field(None, max_length=3, description="ISO 4217 currency code")
    pending_outgoing_payments_count: int = Field(..., description="Number of pending outgoing payments")
    pending_outgoing_payments_amount_minor: int | None = Field(None, description="Total pending amount in minor units")
    as_of_timestamp: datetime | None = Field(None, description="Balance freshness timestamp")
    freshness_status: str = Field(..., description="within_target, breached, unknown")
    item_state: str = Field(..., description="available or partial")
    payment_source_eligible: bool = Field(..., description="True if user has pay entitlement")
    
    model_config = ConfigDict(from_attributes=True)


class BusinessAccountsResponse(BaseModel):
    """Business accounts overview for active business profile."""
    accounts: list[BusinessAccountItem] = Field(..., description="Business accounts")
    business_name: str = Field(..., max_length=160, description="Business name")
    overview_state: str = Field(..., description="complete, partial, or unavailable")
    
    model_config = ConfigDict(from_attributes=True)

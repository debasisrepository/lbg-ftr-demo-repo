"""Profile domain schemas."""
from pydantic import BaseModel, Field


class ProfileInfo(BaseModel):
    """Profile information in list."""
    profile_id: int = Field(..., description="Profile ID")
    profile_type: str = Field(..., description="Profile type (personal/business)")
    display_name: str = Field(..., description="Display name")
    business_name: str | None = Field(None, description="Business name if business profile")
    can_view_accounts: bool = Field(..., description="Whether can view accounts")
    can_create_payee: bool = Field(..., description="Whether can create payees")
    can_approve_payment: bool = Field(..., description="Whether can approve payments")


class ProfileListResponse(BaseModel):
    """Response for GET /profiles."""
    active_profile_id: int | None = Field(None, description="Active profile ID")
    profiles: list[ProfileInfo] = Field(..., description="Available profiles")


class ActivateProfileRequest(BaseModel):
    """Request to activate a profile."""
    profile_id: int = Field(..., description="Profile ID to activate")


class ActiveProfileResponse(BaseModel):
    """Response for POST /profiles/activate."""
    profile_id: int = Field(..., description="Activated profile ID")
    profile_type: str = Field(..., description="Profile type")
    display_name: str = Field(..., description="Display name")

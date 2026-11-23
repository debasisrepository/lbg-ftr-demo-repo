"""
Authentication schemas for sign-in and session management.
Requirement: FR-AUTH-003, FR-AUTH-006
"""
from datetime import datetime
from typing import Literal

from pydantic import BaseModel, Field


class LoginRequest(BaseModel):
    """Request schema for passcode sign-in."""
    device_identifier: str = Field(..., min_length=8, max_length=128, description="Stable identifier of the app installation")
    mobile_platform: Literal["iOS", "Android"] = Field(..., description="Platform of the device")
    passcode: str = Field(..., min_length=4, max_length=12, description="Customer passcode")


class UserSummary(BaseModel):
    """Customer profile summary."""
    id: str = Field(..., description="Customer profile reference ID")
    display_name: str = Field(..., description="Synthetic customer name for the app header")
    profile_type: Literal["personal"] = Field(..., description="Release 1 serves personal profiles only")


class LoginResponse(BaseModel):
    """Response schema for successful sign-in."""
    access_token: str = Field(..., description="Bearer token")
    token_type: Literal["Bearer"] = Field(default="Bearer", description="Always Bearer")
    expires_in: int = Field(..., description="Seconds until absolute expiry")
    expires_at: datetime = Field(..., description="Absolute expiry")
    inactivity_timeout_seconds: int = Field(..., description="Seconds of inactivity after which the session ends")
    session_id: str = Field(..., description="User session ID")
    user: UserSummary = Field(..., description="Signed-in customer")


class SessionResponse(BaseModel):
    """Response schema for session validation."""
    authenticated: bool = Field(default=True, description="Always true on a 200")
    session_id: str = Field(..., description="User session ID")
    issued_at: datetime = Field(..., description="Session start")
    expires_at: datetime = Field(..., description="Absolute expiry")
    last_activity_at: datetime = Field(..., description="Last protected request")
    inactivity_expires_at: datetime = Field(..., description="last_activity_at plus the inactivity timeout")
    user: UserSummary = Field(..., description="Signed-in customer")

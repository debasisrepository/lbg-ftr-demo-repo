"""Auth schemas."""
from datetime import datetime

from pydantic import BaseModel


class LoginRequest(BaseModel):
    """Login request."""

    username: str
    password: str
    channel: str = "mobile_app"


class LoginResponse(BaseModel):
    """Login response."""

    access_token: str
    token_type: str = "bearer"
    expires_at: datetime
    inactivity_timeout_seconds: int
    session_id: str
    user: "UserSummary"


class UserSummary(BaseModel):
    """User summary."""

    id: str
    username: str
    email: str | None
    display_name: str | None
    scope: str
    customer_party_id: str | None
    brand: str | None


class RefreshResponse(BaseModel):
    """Token refresh response."""

    access_token: str
    token_type: str = "bearer"
    expires_at: datetime


class MeResponse(BaseModel):
    """Current user response."""

    user: UserSummary
    session_id: str
    expires_at: datetime
    last_activity_at: datetime

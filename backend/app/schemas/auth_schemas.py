from datetime import datetime
from pydantic import BaseModel, Field


class LoginRequest(BaseModel):
    """Login request payload."""
    username: str = Field(..., min_length=1, max_length=255)
    password: str = Field(..., min_length=1, max_length=255)


class UserInfo(BaseModel):
    """User information in token response."""
    id: int
    username: str
    status: str


class TokenResponse(BaseModel):
    """JWT token response."""
    access_token: str
    token_type: str = "Bearer"
    expires_in_seconds: int
    session_id: int
    step_up_required: bool
    available_step_up_methods: list[str]
    active_profile_id: int | None = None
    user: UserInfo


class LogoutResponse(BaseModel):
    """Logout response."""
    message: str

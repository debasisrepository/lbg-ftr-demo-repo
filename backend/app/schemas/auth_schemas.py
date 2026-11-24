"""Auth endpoint schemas."""
from datetime import datetime
from typing import List

from pydantic import BaseModel, Field, field_serializer


class RoleContextSchema(BaseModel):
    """Role context schema."""
    role_code: str
    role_label: str
    allowed_widgets: List[str]
    entitled_queue_states: List[str]
    allowed_actions: List[str]
    can_view_sensitive_fields: bool


class UserSchema(BaseModel):
    """User schema."""
    user_id: str = Field(serialization_alias="id")
    username: str
    display_name: str
    email: str


class LoginRequest(BaseModel):
    """Login request."""
    username: str = Field(..., min_length=1)
    password: str = Field(..., min_length=1)


class TokenResponse(BaseModel):
    """Token response."""
    access_token: str
    token_type: str
    expires_in: int
    inactivity_timeout_seconds: int
    session_id: str
    user: UserSchema
    active_role_code: str
    available_roles: List[RoleContextSchema]


class LogoutResponse(BaseModel):
    """Logout response."""
    session_id: str
    revoked_at: datetime


class SessionResponse(BaseModel):
    """Session response."""
    session_id: str
    user: UserSchema
    active_role_code: str
    available_roles: List[RoleContextSchema]
    issued_at: datetime
    expires_at: datetime
    seconds_until_inactivity_timeout: int

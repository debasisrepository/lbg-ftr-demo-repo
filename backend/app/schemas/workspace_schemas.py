"""Workspace endpoint schemas."""
from datetime import datetime
from typing import Any, Dict, List

from pydantic import BaseModel


class RoleOptionSchema(BaseModel):
    """Role option schema."""
    role_code: str
    role_label: str


class WidgetSchema(BaseModel):
    """Widget schema."""
    widget_code: str
    widget_label: str
    widget_data: Dict[str, Any]


class LandingResponse(BaseModel):
    """Landing workspace response."""
    active_role_code: str
    active_role_label: str
    available_roles: List[RoleOptionSchema]
    allowed_actions: List[str]
    widgets: List[WidgetSchema]
    data_freshness: datetime
    generated_at: datetime


class ActiveRoleRequest(BaseModel):
    """Active role switch request."""
    role_code: str


class ActiveRoleResponse(BaseModel):
    """Active role switch response."""
    previous_role_code: str
    active_role_code: str
    allowed_actions: List[str]
    switched_at: datetime

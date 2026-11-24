"""Request context for carrying user and role information."""
from dataclasses import dataclass


@dataclass
class RoleContext:
    """Role-based authorization context."""

    role_code: str
    role_label: str
    allowed_widgets: list[str]
    entitled_queue_states: list[str]
    allowed_actions: list[str]
    can_view_sensitive_fields: bool

    def can(self, action: str) -> bool:
        """Check if role allows action."""
        return action in self.allowed_actions


@dataclass
class RequestContext:
    """Request context with user and role."""

    user_id: str
    username: str
    display_name: str
    email: str
    session_id: str
    active_role: RoleContext
    available_roles: list[RoleContext]
    correlation_id: str

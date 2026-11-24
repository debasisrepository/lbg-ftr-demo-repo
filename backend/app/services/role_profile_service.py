"""Role profile service."""
from typing import List

from sqlalchemy.orm import Session

from app.core.context import RoleContext
from app.core.errors import AuthorizationError
from app.repositories.role_repository import RoleRepository


class RoleProfileService:
    """Service for role profile operations."""

    def __init__(self, db: Session):
        self.db = db
        self.role_repo = RoleRepository(db)

    def resolve(self, user_id: str, role_code: str) -> RoleContext:
        """Resolve role context for user.
        
        Args:
            user_id: User ID
            role_code: Role code to resolve
            
        Returns:
            RoleContext
            
        Raises:
            AuthorizationError: If user doesn't have role
        """
        # Get user's role assignments
        assignments = self.role_repo.get_assignments_by_user(user_id)

        # Check user has this role
        has_role = any(a.role_code == role_code for a in assignments)
        if not has_role:
            raise AuthorizationError(
                f"User does not have role {role_code}",
                code="forbidden_role",
            )

        # Get role profile
        profile = self.role_repo.get_profile_by_code(role_code)
        if not profile:
            raise AuthorizationError(
                f"Role profile {role_code} not found",
                code="role_not_found",
            )

        return RoleContext(
            role_code=profile.role_code,
            role_label=profile.role_label,
            allowed_widgets=profile.allowed_widgets_json.get("codes", []) if profile.allowed_widgets_json else [],
            entitled_queue_states=profile.entitled_queue_states_json.get("states", []) if profile.entitled_queue_states_json else [],
            allowed_actions=profile.allowed_actions_json.get("actions", []) if profile.allowed_actions_json else [],
            can_view_sensitive_fields=profile.can_view_sensitive_fields,
        )

    def get_available_roles(self, user_id: str) -> List[RoleContext]:
        """Get all available roles for user.
        
        Args:
            user_id: User ID
            
        Returns:
            List of RoleContext
        """
        assignments = self.role_repo.get_assignments_by_user(user_id)

        contexts = []
        for assignment in assignments:
            profile = self.role_repo.get_profile_by_code(assignment.role_code)
            if profile:
                contexts.append(
                    RoleContext(
                        role_code=profile.role_code,
                        role_label=profile.role_label,
                        allowed_widgets=profile.allowed_widgets_json.get("codes", []) if profile.allowed_widgets_json else [],
                        entitled_queue_states=profile.entitled_queue_states_json.get("states", []) if profile.entitled_queue_states_json else [],
                        allowed_actions=profile.allowed_actions_json.get("actions", []) if profile.allowed_actions_json else [],
                        can_view_sensitive_fields=profile.can_view_sensitive_fields,
                    )
                )

        return contexts

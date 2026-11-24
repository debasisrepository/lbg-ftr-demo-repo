"""Role repository."""
import uuid
from typing import List, Optional

from sqlalchemy.orm import Session

from app.models.roles import RoleAssignment, RoleProfile


class RoleRepository:
    """Repository for role operations."""

    def __init__(self, db: Session):
        self.db = db

    def get_profile_by_code(self, role_code: str) -> Optional[RoleProfile]:
        """Get role profile by code."""
        return (
            self.db.query(RoleProfile)
            .filter(RoleProfile.role_code == role_code)
            .first()
        )

    def get_assignments_by_user(self, user_id: str) -> List[RoleAssignment]:
        """Get active role assignments for user."""
        user_uuid = uuid.UUID(user_id) if isinstance(user_id, str) else user_id
        return (
            self.db.query(RoleAssignment)
            .filter(
                RoleAssignment.user_id == user_uuid,
                RoleAssignment.assignment_status == "active",
            )
            .all()
        )

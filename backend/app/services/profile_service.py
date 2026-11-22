"""Profile service"""
import uuid

from sqlalchemy.orm import Session

from app.core.errors import AuthorizationError, ResourceNotFoundError
from app.repositories.profile_repository import ProfileRepository


class ProfileService:
    """Service for profile operations"""

    def __init__(self):
        self.profile_repo = ProfileRepository()

    def get_profiles_for_customer(self, db: Session, customer_id: uuid.UUID) -> list:
        """Get all profiles for a customer"""
        return self.profile_repo.get_by_customer_id(db, customer_id)

    def get_profile_by_id(self, db: Session, profile_id: uuid.UUID):
        """Get a profile by ID"""
        return self.profile_repo.get_by_id(db, profile_id)

    def set_active_profile(
        self,
        db: Session,
        session_id: uuid.UUID,
        customer_id: uuid.UUID,
        profile_id: uuid.UUID
    ) -> None:
        """
        Set active profile for session.

        Raises:
            ResourceNotFoundError: If profile not found
            AuthorizationError: If profile doesn't belong to customer
        """
        # Verify profile exists and belongs to customer
        if not self.profile_repo.belongs_to_customer(db, profile_id, customer_id):
            raise AuthorizationError("Profile does not belong to customer")

        # Update session's active profile
        from app.repositories.session_repository import SessionRepository
        session_repo = SessionRepository(db)
        session = session_repo.get_by_id(session_id)
        if not session:
            raise ResourceNotFoundError("Session not found")

        session.active_profile_id = profile_id
        db.flush()

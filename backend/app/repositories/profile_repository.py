"""Repository for profile-related database operations."""
from datetime import datetime, timezone
from sqlalchemy.orm import Session
from app.models.profiles import UserProfile, ProfileEntitlement


class ProfileRepository:
    """Repository for profile operations."""

    def __init__(self, db: Session):
        self.db = db

    def get_profiles_by_user(self, user_identity_id: int) -> list[UserProfile]:
        """Get all profiles for a user."""
        return self.db.query(UserProfile).filter(
            UserProfile.user_identity_id == user_identity_id
        ).all()

    def get_profile_by_id(self, profile_id: int) -> UserProfile | None:
        """Get profile by ID."""
        return self.db.query(UserProfile).filter(
            UserProfile.id == profile_id
        ).first()

    def get_entitlements_by_profile(self, profile_id: int) -> list[ProfileEntitlement]:
        """Get all entitlements for a profile."""
        return self.db.query(ProfileEntitlement).filter(
            ProfileEntitlement.profile_id == profile_id
        ).all()

    def update_active_profile(self, session_id: int, profile_id: int) -> None:
        """Update active profile for a session."""
        from app.models.auth import AuthSession
        session = self.db.query(AuthSession).filter(
            AuthSession.id == session_id
        ).first()
        if session:
            session.active_profile_id = profile_id
            session.updated_at = datetime.now(timezone.utc)
            self.db.commit()

"""User repository."""
from datetime import datetime
from typing import Optional

from sqlalchemy.orm import Session

from app.models.users import LoginAttempt, User


class UserRepository:
    """Repository for user operations."""

    def __init__(self, db: Session):
        self.db = db

    def get_by_username(self, username: str) -> Optional[User]:
        """Get user by username."""
        return self.db.query(User).filter(User.username == username).first()

    def get_by_id(self, user_id: str) -> Optional[User]:
        """Get user by ID."""
        import uuid as uuid_module
        user_uuid = uuid_module.UUID(user_id) if isinstance(user_id, str) else user_id
        return self.db.query(User).filter(User.id == user_uuid).first()

    def create_login_attempt(self, login_attempt: LoginAttempt) -> LoginAttempt:
        """Create a login attempt record."""
        self.db.add(login_attempt)
        self.db.flush()
        return login_attempt

    def count_recent_failed_attempts(self, username: str, since: "datetime") -> int:
        """Count recent failed login attempts for username."""
        return (
            self.db.query(LoginAttempt)
            .filter(
                LoginAttempt.username_attempted == username,
                LoginAttempt.succeeded == False,  # noqa: E712
                LoginAttempt.attempted_at >= since,
            )
            .count()
        )

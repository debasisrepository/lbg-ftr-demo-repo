"""Session repository."""
from datetime import datetime
from typing import Optional

from sqlalchemy.orm import Session

from app.models.sessions import UserSession


class SessionRepository:
    """Repository for session operations."""

    def __init__(self, db: Session):
        self.db = db

    def create(self, session: UserSession) -> UserSession:
        """Create a new session."""
        self.db.add(session)
        self.db.flush()
        return session

    def get_by_token_hash(self, token_hash: str) -> Optional[UserSession]:
        """Get session by token hash."""
        return (
            self.db.query(UserSession)
            .filter(UserSession.token_hash == token_hash)
            .first()
        )

    def update_activity(self, session: UserSession, now: datetime) -> None:
        """Update last activity timestamp."""
        session.last_activity_at = now
        self.db.flush()

    def update_role(self, session: UserSession, role_code: str) -> None:
        """Update active role."""
        session.active_role_code = role_code
        self.db.flush()

    def revoke(self, session: UserSession, now: datetime, reason: str) -> None:
        """Revoke a session."""
        session.is_revoked = True
        session.revoked_at = now
        session.revoke_reason = reason
        self.db.flush()

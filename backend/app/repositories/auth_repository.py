"""Auth repository."""
import uuid
from datetime import datetime

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.auth import AuthSession, UserAccount


class AuthRepository:
    """Repository for auth operations."""

    def __init__(self, session: Session):
        self.session = session

    def by_username(self, username: str) -> UserAccount | None:
        """Get user by username."""
        return self.session.scalar(select(UserAccount).where(UserAccount.username == username))

    def session_by_id(self, session_id: uuid.UUID) -> AuthSession | None:
        """Get session by ID."""
        return self.session.get(AuthSession, session_id)

    def session_by_token_hash(self, token_hash: str) -> AuthSession | None:
        """Get session by token hash."""
        return self.session.scalar(select(AuthSession).where(AuthSession.token_hash == token_hash))

    def create_session(
        self,
        user_id: uuid.UUID,
        token_hash: str,
        created_at: datetime,
        expires_at: datetime,
        origin_channel: str,
        session_id: uuid.UUID | None = None,
    ) -> AuthSession:
        """Create a new session."""
        session = AuthSession(
            id=session_id or uuid.uuid4(),
            user_id=user_id,
            token_hash=token_hash,
            created_at=created_at,
            expires_at=expires_at,
            last_activity_at=created_at,
            origin_channel=origin_channel,
        )
        self.session.add(session)
        return session

    def touch_session(self, session: AuthSession, now: datetime) -> None:
        """Update session last activity."""
        session.last_activity_at = now

    def revoke_session(self, session: AuthSession, now: datetime, reason: str) -> None:
        """Revoke a session."""
        session.revoked_at = now
        session.revoke_reason = reason

    def increment_failed_login(self, user: UserAccount) -> None:
        """Increment failed login count."""
        user.failed_login_count += 1

    def lock_account(self, user: UserAccount, locked_until: datetime) -> None:
        """Lock an account."""
        user.locked_until = locked_until

    def reset_failed_login(self, user: UserAccount) -> None:
        """Reset failed login count."""
        user.failed_login_count = 0
        user.locked_until = None

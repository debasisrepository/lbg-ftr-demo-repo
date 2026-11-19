from datetime import datetime, timezone
from sqlalchemy.orm import Session
from app.models.auth import UserIdentity, AuthSession, RegisteredDevice
from app.common.enums import UserStatus, SessionState


class AuthRepository:
    """Repository for authentication-related database operations."""

    def __init__(self, db: Session):
        self.db = db

    def get_user_by_username(self, username: str) -> UserIdentity | None:
        """Get user identity by username."""
        return self.db.query(UserIdentity).filter(
            UserIdentity.username == username
        ).first()

    def create_session(
        self,
        user_identity_id: int,
        token_hash: str,
        expires_at: datetime,
        active_profile_id: int | None = None
    ) -> AuthSession:
        """Create a new auth session."""
        now = datetime.now(timezone.utc)
        session = AuthSession(
            user_identity_id=user_identity_id,
            token_hash=token_hash,
            session_state=SessionState.ACTIVE.value,
            issued_at=now,
            expires_at=expires_at,
            last_activity_at=now,
            active_profile_id=active_profile_id,
            created_at=now,
            updated_at=now
        )
        self.db.add(session)
        self.db.commit()
        self.db.refresh(session)
        return session

    def get_session_by_id(self, session_id: int) -> AuthSession | None:
        """Get auth session by ID."""
        return self.db.query(AuthSession).filter(
            AuthSession.id == session_id
        ).first()

    def get_session_by_token_hash(self, token_hash: str) -> AuthSession | None:
        """Get active auth session by token hash."""
        return self.db.query(AuthSession).filter(
            AuthSession.token_hash == token_hash,
            AuthSession.session_state == SessionState.ACTIVE.value
        ).first()

    def revoke_session(self, session_id: int) -> None:
        """Revoke an auth session."""
        session = self.db.query(AuthSession).filter(
            AuthSession.id == session_id
        ).first()
        if session:
            session.session_state = SessionState.REVOKED.value
            session.updated_at = datetime.now(timezone.utc)
            self.db.commit()

    def update_session_activity(self, session_id: int) -> None:
        """Update last activity timestamp for session."""
        session = self.db.query(AuthSession).filter(
            AuthSession.id == session_id
        ).first()
        if session:
            session.last_activity_at = datetime.now(timezone.utc)
            session.updated_at = datetime.now(timezone.utc)
            self.db.commit()

    def get_registered_devices(self, user_identity_id: int) -> list[RegisteredDevice]:
        """Get all registered devices for a user."""
        return self.db.query(RegisteredDevice).filter(
            RegisteredDevice.user_identity_id == user_identity_id
        ).all()

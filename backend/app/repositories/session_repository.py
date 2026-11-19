"""Session repository for session lifecycle management"""
import uuid
from datetime import UTC, datetime, timedelta

from sqlalchemy import select
from sqlalchemy.orm import Session as DBSession

from ..models.session import Session


class SessionRepository:
    """Session data access"""

    def __init__(self, db: DBSession):
        self.db = db

    def get_by_id(self, session_id: uuid.UUID) -> Session | None:
        """Get session by ID"""
        return self.db.get(Session, session_id)

    def get_by_token_hash(self, token_hash: str) -> Session | None:
        """Get session by token hash"""
        stmt = select(Session).where(
            Session.session_token_hash == token_hash,
            Session.ended_at.is_(None)
        )
        result = self.db.execute(stmt)
        return result.scalar_one_or_none()

    def create(
        self,
        customer_id: uuid.UUID,
        device_id: uuid.UUID | None,
        session_token_hash: str,
        auth_level: str,
        started_at: datetime,
        expires_at: datetime,
        inactivity_timeout_seconds: int,
        correlation_id: str
    ) -> Session:
        """Create a new session"""
        session = Session(
            session_id=uuid.uuid4(),
            customer_id=customer_id,
            device_id=device_id,
            active_profile_id=None,
            session_token_hash=session_token_hash,
            auth_level=auth_level,
            started_at=started_at,
            last_activity_at=started_at,
            expires_at=expires_at,
            inactivity_timeout_seconds=inactivity_timeout_seconds,
            correlation_id=correlation_id
        )
        self.db.add(session)
        self.db.flush()
        return session

    def update_auth_level(self, session: Session, auth_level: str) -> None:
        """Update session auth level"""
        session.auth_level = auth_level
        session.updated_at = datetime.now(UTC)
        self.db.flush()

    def set_active_profile(self, session: Session, profile_id: uuid.UUID | None) -> None:
        """Set active profile for session"""
        session.active_profile_id = profile_id
        session.updated_at = datetime.now(UTC)
        self.db.flush()

    def update_activity(self, session: Session) -> None:
        """Update last activity timestamp"""
        now = datetime.now(UTC)
        session.last_activity_at = now
        # Extend expiry based on inactivity timeout
        session.expires_at = now + timedelta(seconds=session.inactivity_timeout_seconds)
        session.updated_at = now
        self.db.flush()

    def end_session(self, session: Session, end_reason: str) -> None:
        """End a session"""
        now = datetime.now(UTC)
        session.ended_at = now
        session.end_reason = end_reason
        session.updated_at = now
        self.db.flush()

    def extend_session(self, session: Session, extension_seconds: int) -> None:
        """Extend session expiry"""
        now = datetime.now(UTC)
        session.expires_at = now + timedelta(seconds=extension_seconds)
        session.last_activity_at = now
        session.updated_at = now
        self.db.flush()

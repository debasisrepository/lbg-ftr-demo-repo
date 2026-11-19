"""Session management service"""
import uuid
from datetime import UTC, datetime

from sqlalchemy.orm import Session

from ..core.errors import AuthenticationError
from ..repositories.session_repository import SessionRepository
from ..schemas.auth_schemas import ExtendSessionResponse, SignOutResponse


class SessionService:
    """Session lifecycle management"""

    def __init__(self, db: Session):
        self.db = db
        self.session_repo = SessionRepository(db)

    def extend_session(self, session_id: uuid.UUID) -> ExtendSessionResponse:
        """Extend session expiry (inactivity reset)"""
        session = self.session_repo.get_by_id(session_id)

        if not session:
            raise AuthenticationError("Session not found")

        if session.ended_at is not None:
            raise AuthenticationError("Session has ended")

        # Ensure timezone-aware comparison
        now = datetime.now(UTC)
        session_expires = session.expires_at if session.expires_at.tzinfo else session.expires_at.replace(tzinfo=UTC)
        if now > session_expires:
            self.session_repo.end_session(session, 'expired')
            self.db.commit()
            raise AuthenticationError("Session has expired")

        # Update activity and extend expiry
        self.session_repo.update_activity(session)
        self.db.commit()

        return ExtendSessionResponse(
            session_id=str(session.session_id),
            expires_at=session.expires_at,
            inactivity_timeout_seconds=session.inactivity_timeout_seconds
        )

    def sign_out(self, session_id: uuid.UUID) -> SignOutResponse:
        """End session (sign out)"""
        session = self.session_repo.get_by_id(session_id)

        if not session:
            # Already signed out or invalid session
            return SignOutResponse(message="Signed out successfully")

        if session.ended_at is None:
            self.session_repo.end_session(session, 'logout')
            self.db.commit()

        return SignOutResponse(message="Signed out successfully")

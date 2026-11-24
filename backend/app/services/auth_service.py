"""Authentication service."""
import uuid
from datetime import datetime, timedelta
from typing import Optional

from sqlalchemy.orm import Session

from app.core.clock import Clock
from app.core.config import settings
from app.core.errors import AuthenticationError, RateLimitError
from app.core.security import (
    create_access_token,
    decode_access_token,
    hash_token,
    verify_password,
)
from app.models.sessions import UserSession
from app.models.users import LoginAttempt, User
from app.repositories.session_repository import SessionRepository
from app.repositories.user_repository import UserRepository


class AuthService:
    """Service for authentication operations."""

    def __init__(self, db: Session, clock: Clock):
        self.db = db
        self.clock = clock
        self.user_repo = UserRepository(db)
        self.session_repo = SessionRepository(db)

    def login(
        self,
        username: str,
        password: str,
        active_role_code: str,
        client_ip: str,
        correlation_id: str,
    ) -> tuple[str, UserSession]:
        """Authenticate user and create session.
        
        Args:
            username: Username
            password: Plain text password
            active_role_code: Initial active role
            client_ip: Client IP address
            correlation_id: Request correlation ID
            
        Returns:
            Tuple of (access_token, session)
            
        Raises:
            AuthenticationError: If credentials invalid or account locked
            RateLimitError: If rate limit exceeded
        """
        now = self.clock.now()

        # Check rate limit
        if settings.rate_limit_enabled:
            window_start = now - timedelta(minutes=settings.rate_limit_window_minutes)
            failed_attempts = self.user_repo.count_recent_failed_attempts(username, window_start)

            if failed_attempts >= settings.rate_limit_max_attempts:
                self._record_attempt(username, None, now, False, "rate_limited", client_ip, correlation_id)
                self.db.commit()
                raise RateLimitError(
                    "Too many failed login attempts. Try again later."
                )

        # Get user
        user = self.user_repo.get_by_username(username)

        if not user:
            self._record_attempt(username, None, now, False, "user_not_found", client_ip, correlation_id)
            self.db.commit()
            raise AuthenticationError("Invalid credentials", code="invalid_credentials")

        # Check account status
        if user.status != "active":
            self._record_attempt(username, user.id, now, False, f"account_{user.status}", client_ip, correlation_id)
            self.db.commit()
            raise AuthenticationError(f"Account is {user.status}", code=f"account_{user.status}")

        # Verify password
        if not verify_password(password, user.password_hash):
            self._record_attempt(username, user.id, now, False, "invalid_password", client_ip, correlation_id)
            self.db.commit()
            raise AuthenticationError("Invalid credentials", code="invalid_credentials")

        # Create session
        session_id = str(uuid.uuid4())
        expires_at = now + timedelta(minutes=settings.jwt_expiry_minutes)

        # Create token
        token = create_access_token(str(user.id), session_id, timedelta(minutes=settings.jwt_expiry_minutes))
        token_hash_value = hash_token(token)

        session = UserSession(
            id=uuid.uuid4(),
            created_at=now,
            updated_at=now,
            user_id=user.id,
            token_hash=token_hash_value,
            active_role_code=active_role_code,
            issued_at=now,
            expires_at=expires_at,
            last_activity_at=now,
            inactivity_timeout_seconds=settings.inactivity_timeout_seconds,
            is_revoked=False,
            client_ip=client_ip,
            correlation_id=correlation_id,
        )

        session = self.session_repo.create(session)

        # Record successful attempt
        self._record_attempt(username, user.id, now, True, None, client_ip, correlation_id)
        
        # Commit all changes
        self.db.commit()

        return token, session

    def logout(self, token: str, correlation_id: str) -> UserSession:
        """Logout user and revoke session.
        
        Args:
            token: Access token
            correlation_id: Request correlation ID
            
        Returns:
            Revoked session
            
        Raises:
            AuthenticationError: If session invalid
        """
        now = self.clock.now()
        session = self._validate_token_internal(token, now)

        self.session_repo.revoke(session, now, "user_logout")
        self.db.commit()

        return session

    def validate_token(self, token: str) -> tuple[User, UserSession]:
        """Validate token and return user and session.
        
        Args:
            token: Access token
            
        Returns:
            Tuple of (user, session)
            
        Raises:
            AuthenticationError: If session invalid or expired
        """
        now = self.clock.now()
        session = self._validate_token_internal(token, now)

        # Update activity
        self.session_repo.update_activity(session, now)
        self.db.commit()

        # Get user
        user = self.user_repo.get_by_id(str(session.user_id))
        if not user:
            raise AuthenticationError("User not found", code="user_not_found")

        return user, session

    def _validate_token_internal(self, token: str, now: datetime) -> UserSession:
        """Internal token validation."""
        # Decode token
        try:
            payload = decode_access_token(token)
        except Exception:
            raise AuthenticationError("Invalid token", code="invalid_token")

        session_id = payload.get("jti")  # JWT ID contains session_id
        if not session_id:
            raise AuthenticationError("Invalid token", code="invalid_token")

        # Get session by token hash
        token_hash_value = hash_token(token)
        session = self.session_repo.get_by_token_hash(token_hash_value)

        if not session:
            raise AuthenticationError("Session not found", code="session_invalid")

        # Check revoked
        if session.is_revoked:
            raise AuthenticationError("Session revoked", code="session_revoked")

        # Ensure timezone-aware datetimes (SQLite may strip timezone info)
        from datetime import timezone as tz
        if session.expires_at.tzinfo is None:
            session.expires_at = session.expires_at.replace(tzinfo=tz.utc)
        if session.last_activity_at.tzinfo is None:
            session.last_activity_at = session.last_activity_at.replace(tzinfo=tz.utc)

        # Check expiry
        if session.expires_at < now:
            raise AuthenticationError("Session expired", code="session_expired")

        # Check inactivity timeout
        inactivity_cutoff = now - timedelta(seconds=session.inactivity_timeout_seconds)
        if session.last_activity_at < inactivity_cutoff:
            self.session_repo.revoke(session, now, "inactivity_timeout")
            self.db.commit()
            raise AuthenticationError("Session expired due to inactivity", code="session_expired")

        return session

    def _record_attempt(
        self,
        username: str,
        user_id: Optional[str],
        attempted_at: datetime,
        succeeded: bool,
        failure_reason: Optional[str],
        client_ip: str,
        correlation_id: str,
    ) -> None:
        """Record login attempt."""
        attempt = LoginAttempt(
            id=uuid.uuid4(),
            created_at=attempted_at,
            updated_at=attempted_at,
            username_attempted=username,
            user_id=uuid.UUID(user_id) if user_id and isinstance(user_id, str) else user_id,
            attempted_at=attempted_at,
            succeeded=succeeded,
            failure_reason=failure_reason,
            client_ip=client_ip,
            correlation_id=correlation_id,
        )

        self.user_repo.create_login_attempt(attempt)

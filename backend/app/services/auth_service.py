"""Auth service."""
import uuid
from datetime import timedelta

from app.config import settings
from app.core.clock import Clock
from app.core.errors import AuthorizationError
from app.core.security import create_jwt, hash_token, verify_password
from app.repositories.auth_repository import AuthRepository
from app.schemas.auth import LoginResponse, MeResponse, RefreshResponse, UserSummary


class AuthService:
    """Authentication service."""

    def __init__(self, repo: AuthRepository):
        self.repo = repo

    def login(self, username: str, password: str, channel: str) -> LoginResponse:
        """Authenticate user and create session."""
        user = self.repo.by_username(username)
        if not user:
            raise AuthorizationError("Invalid credentials")

        # Check if account is locked
        now = Clock.utcnow()
        if user.locked_until and user.locked_until > now:
            raise AuthorizationError("Account is locked")

        # Verify password
        if not verify_password(password, user.hashed_password):
            self.repo.increment_failed_login(user)
            if user.failed_login_count >= settings.login_failure_threshold:
                lock_until = now + timedelta(minutes=settings.login_lock_minutes)
                self.repo.lock_account(user, lock_until)
            raise AuthorizationError("Invalid credentials")

        # Check if user is active
        if not user.is_active:
            raise AuthorizationError("Account is inactive")

        # Reset failed login count
        self.repo.reset_failed_login(user)

        # Create JWT and session
        session_id = uuid.uuid4()
        token, expires_at = create_jwt(str(user.id), str(session_id), user.scope)
        token_hash_str = hash_token(token)

        session = self.repo.create_session(
            user_id=user.id,
            token_hash=token_hash_str,
            created_at=now,
            expires_at=expires_at,
            origin_channel=channel,
            session_id=session_id,
        )

        user_summary = UserSummary(
            id=str(user.id),
            username=user.username,
            email=user.email,
            display_name=user.display_name,
            scope=user.scope,
            customer_party_id=user.customer_party_id,
            brand=user.brand,
        )

        return LoginResponse(
            access_token=token,
            token_type="bearer",
            expires_at=expires_at,
            inactivity_timeout_seconds=settings.session_inactivity_minutes * 60,
            session_id=str(session.id),
            user=user_summary,
        )

    def refresh(self, session_id: uuid.UUID) -> RefreshResponse:
        """Refresh session token."""
        from app.models.auth import UserAccount

        session = self.repo.session_by_id(session_id)
        if not session:
            raise AuthorizationError("Session not found")

        if session.revoked_at:
            raise AuthorizationError("Session revoked")

        now = Clock.utcnow()
        max_expires = session.created_at + timedelta(minutes=settings.session_max_minutes)
        if now >= max_expires:
            raise AuthorizationError("Session maximum lifetime reached")

        # Get user
        user = self.repo.session.get(UserAccount, session.user_id)
        if not user:
            raise AuthorizationError("User not found")

        # Create new token
        token, expires_at = create_jwt(str(session.user_id), str(session.id), user.scope)
        token_hash_str = hash_token(token)

        # Update session
        session.token_hash = token_hash_str
        session.expires_at = expires_at
        session.last_activity_at = now

        return RefreshResponse(access_token=token, token_type="bearer", expires_at=expires_at)

    def logout(self, session_id: uuid.UUID) -> None:
        """Logout and revoke session."""
        session = self.repo.session_by_id(session_id)
        if session and not session.revoked_at:
            now = Clock.utcnow()
            self.repo.revoke_session(session, now, "logout")

    def get_me(self, session_id: uuid.UUID) -> MeResponse:
        """Get current user info."""
        from app.models.auth import UserAccount

        session = self.repo.session_by_id(session_id)
        if not session:
            raise AuthorizationError("Session not found")

        if session.revoked_at:
            raise AuthorizationError("Session revoked")

        # Touch session
        now = Clock.utcnow()
        self.repo.touch_session(session, now)

        # Get user
        user = self.repo.session.get(UserAccount, session.user_id)
        if not user:
            raise AuthorizationError("User not found")

        user_summary = UserSummary(
            id=str(user.id),
            username=user.username,
            email=user.email,
            display_name=user.display_name,
            scope=user.scope,
            customer_party_id=user.customer_party_id,
            brand=user.brand,
        )

        return MeResponse(
            user=user_summary,
            session_id=str(session.id),
            expires_at=session.expires_at,
            last_activity_at=session.last_activity_at,
        )

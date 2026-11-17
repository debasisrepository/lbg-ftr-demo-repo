from sqlalchemy.orm import Session
from datetime import timedelta, datetime, timezone
from app.auth.repository import AuthRepository
from app.auth.models import AppUser, AuthSession, LoginAttempt
from app.auth.passwords import PasswordHasher
from app.auth.tokens import TokenService
from app.auth.rate_limit import LoginRateLimiter
from app.core.clock import Clock
from app.core.ids import IdGenerator
from app.core.errors import AuthenticationError, RateLimitError
from app.config import settings
import uuid


class AuthService:
    def __init__(self, db: Session):
        self.db = db
        self.repo = AuthRepository(db)

    def login(self, email: str, password: str, ip_address: str | None = None, user_agent: str | None = None) -> tuple[str, AppUser]:
        source_key = ip_address or "unknown"

        allowed, reason = LoginRateLimiter.check_rate_limit(self.db, source_key, email)
        if not allowed:
            self._record_attempt(email, "rate_limited", "rate_limit_exceeded", ip_address, user_agent)
            raise RateLimitError("Too many failed login attempts. Please try again later.")

        user = self.repo.get_user_by_email(email)
        if not user:
            self._record_attempt(email, "failed", "unknown_user", ip_address, user_agent)
            raise AuthenticationError("Invalid credentials")

        if user.account_locked_until and user.account_locked_until > Clock.utc_now():
            self._record_attempt(email, "locked", "account_locked", ip_address, user_agent)
            raise AuthenticationError("Account is locked")

        if not PasswordHasher.verify_password(password, user.hashed_password):
            self.repo.increment_failed_login(user)
            self._record_attempt(email, "failed", "wrong_password", ip_address, user_agent)
            raise AuthenticationError("Invalid credentials")

        if not user.is_active:
            self._record_attempt(email, "failed", "inactive_account", ip_address, user_agent)
            raise AuthenticationError("Invalid credentials")

        now = Clock.utc_now()
        session_id = IdGenerator.uuid4()
        token = TokenService.create_token(user.id, session_id)
        token_hash = TokenService.hash_token(token)

        session = AuthSession(
            id=session_id,
            user_id=user.id,
            token_hash=token_hash,
            ip_address=ip_address,
            user_agent=user_agent,
            last_activity_at=now,
            expires_at=now + timedelta(seconds=settings.jwt_expiry_seconds),
            revoked=False,
            created_at=now,
        )
        self.repo.create_session(session)
        self.repo.update_user_login_success(user, now)
        self._record_attempt(email, "success", None, ip_address, user_agent)

        return token, user

    def logout(self, token: str) -> None:
        token_hash = TokenService.hash_token(token)
        session = self.repo.get_session_by_token_hash(token_hash)
        if session:
            self.repo.revoke_session(session.id)

    def get_current_user(self, token: str) -> AppUser:
        payload = TokenService.decode_token(token)
        session_id = payload.get("jti")
        user_id = int(payload.get("sub"))

        token_hash = TokenService.hash_token(token)
        session = self.repo.get_session_by_token_hash(token_hash)

        if not session or session.revoked:
            raise AuthenticationError("Invalid session")

        now = Clock.utc_now()
        expires_at = session.expires_at.replace(tzinfo=timezone.utc) if session.expires_at.tzinfo is None else session.expires_at
        last_activity_at = session.last_activity_at.replace(tzinfo=timezone.utc) if session.last_activity_at.tzinfo is None else session.last_activity_at

        if expires_at < now:
            raise AuthenticationError("Session expired")

        if last_activity_at + timedelta(seconds=settings.session_inactivity_seconds) < now:
            raise AuthenticationError("Session expired due to inactivity")

        user = self.repo.get_user_by_id(user_id)
        if not user or not user.is_active:
            raise AuthenticationError("User not found or inactive")

        session.last_activity_at = Clock.utc_now()
        self.db.commit()

        return user

    def _record_attempt(self, email: str, outcome: str, reason_code: str | None, ip_address: str | None, user_agent: str | None) -> None:
        attempt = LoginAttempt(
            id=IdGenerator.uuid4(),
            source_key=ip_address or "unknown",
            username_attempted=email,
            outcome=outcome,
            reason_code=reason_code,
            ip_address=ip_address,
            user_agent=user_agent,
            occurred_at=Clock.utc_now(),
        )
        self.repo.record_login_attempt(attempt)

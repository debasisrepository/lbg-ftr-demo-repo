from datetime import datetime, timedelta, timezone
from sqlalchemy.orm import Session
from app.repositories.auth_repository import AuthRepository
from app.services.audit_service import AuditService
from app.services.telemetry_service import TelemetryService
from app.common.security import verify_password, create_access_token, hash_token
from app.common.enums import UserStatus, JourneyOutcomeCode
from app.common.errors import AuthenticationError, RateLimitError
from app.config import settings
from collections import defaultdict
from threading import Lock


# In-memory rate limiter (simple implementation for demo)
class RateLimiter:
    """Simple in-memory rate limiter for login attempts."""
    
    def __init__(self):
        self.attempts = defaultdict(list)
        self.lock = Lock()
    
    def check_rate_limit(self, key: str, max_attempts: int, window_seconds: int) -> bool:
        """Check if rate limit is exceeded. Returns True if allowed, False if blocked."""
        if not settings.rate_limit_enabled:
            return True
            
        with self.lock:
            now = datetime.now(timezone.utc)
            cutoff = now - timedelta(seconds=window_seconds)
            
            # Clean old attempts
            self.attempts[key] = [t for t in self.attempts[key] if t > cutoff]
            
            # Check limit
            if len(self.attempts[key]) >= max_attempts:
                return False
            
            # Record attempt
            self.attempts[key].append(now)
            return True
    
    def reset(self, key: str | None = None) -> None:
        """Reset rate limiter for testing."""
        with self.lock:
            if key:
                self.attempts.pop(key, None)
            else:
                self.attempts.clear()


# Global rate limiter instance
rate_limiter = RateLimiter()


class AuthService:
    """Service for authentication operations."""

    def __init__(self, db: Session, correlation_id: str):
        self.db = db
        self.correlation_id = correlation_id
        self.auth_repo = AuthRepository(db)
        self.audit_service = AuditService(db)
        self.telemetry_service = TelemetryService(db)

    def login(self, username: str, password: str, client_ip: str) -> tuple[str, int, int]:
        """
        Authenticate user and create session.
        
        Returns (access_token, session_id, active_profile_id).
        Raises AuthenticationError if credentials invalid or account locked.
        Raises RateLimitError if too many failed attempts.
        """
        # Check rate limit
        rate_key = f"login:{client_ip}"
        if not rate_limiter.check_rate_limit(
            rate_key,
            settings.rate_limit_login_attempts,
            settings.rate_limit_login_window_seconds
        ):
            self.telemetry_service.emit_sign_in_event(
                correlation_id=self.correlation_id,
                auth_session_id=None,
                outcome_code=JourneyOutcomeCode.BLOCKED.value,
                failure_reason="rate_limit_exceeded"
            )
            raise RateLimitError("Too many sign-in attempts. Try again shortly.")

        # Get user
        user = self.auth_repo.get_user_by_username(username)
        
        # Generic failure message (don't reveal if user exists)
        generic_error = "We couldn't sign you in with those details."
        
        if not user:
            self.audit_service.log_auth_login_failed(
                correlation_id=self.correlation_id,
                username=username,
                payload={"reason": "user_not_found", "client_ip": client_ip}
            )
            self.telemetry_service.emit_sign_in_event(
                correlation_id=self.correlation_id,
                auth_session_id=None,
                outcome_code=JourneyOutcomeCode.FAILURE.value,
                failure_reason="invalid_credentials"
            )
            raise AuthenticationError(generic_error)

        # Check password
        if not verify_password(password, user.hashed_password):
            self.audit_service.log_auth_login_failed(
                correlation_id=self.correlation_id,
                username=username,
                payload={"reason": "invalid_password", "client_ip": client_ip}
            )
            self.telemetry_service.emit_sign_in_event(
                correlation_id=self.correlation_id,
                auth_session_id=None,
                outcome_code=JourneyOutcomeCode.FAILURE.value,
                failure_reason="invalid_credentials"
            )
            raise AuthenticationError(generic_error)

        # Check user status
        if user.status != UserStatus.ACTIVE.value:
            self.audit_service.log_auth_login_failed(
                correlation_id=self.correlation_id,
                username=username,
                payload={"reason": "account_not_active", "status": user.status, "client_ip": client_ip}
            )
            self.telemetry_service.emit_sign_in_event(
                correlation_id=self.correlation_id,
                auth_session_id=None,
                outcome_code=JourneyOutcomeCode.BLOCKED.value,
                failure_reason="account_not_active"
            )
            raise AuthenticationError(generic_error)

        # Get default profile
        from app.models.profiles import UserProfile
        default_profile = self.db.query(UserProfile).filter(
            UserProfile.user_identity_id == user.id,
            UserProfile.is_default == True
        ).first()
        
        active_profile_id = default_profile.id if default_profile else None

        # Create access token
        access_token = create_access_token(user.id, settings.jwt_expiry_minutes)
        token_hash = hash_token(access_token)
        
        # Create session
        expires_at = datetime.now(timezone.utc) + timedelta(minutes=settings.jwt_expiry_minutes)
        session = self.auth_repo.create_session(
            user_identity_id=user.id,
            token_hash=token_hash,
            expires_at=expires_at,
            active_profile_id=active_profile_id
        )

        # Audit and telemetry
        self.audit_service.log_auth_login_succeeded(
            correlation_id=self.correlation_id,
            auth_session_id=session.id,
            user_identity_id=user.id,
            payload={"client_ip": client_ip}
        )
        self.telemetry_service.emit_sign_in_event(
            correlation_id=self.correlation_id,
            auth_session_id=session.id,
            outcome_code=JourneyOutcomeCode.SUCCESS.value
        )

        return access_token, session.id, active_profile_id

    def logout(self, session_id: int, user_identity_id: int) -> None:
        """Revoke session and log out user."""
        self.auth_repo.revoke_session(session_id)
        self.audit_service.log_auth_logout(
            correlation_id=self.correlation_id,
            auth_session_id=session_id,
            user_identity_id=user_identity_id
        )

    def get_available_sca_methods(self, user_identity_id: int) -> list[str]:
        """Get available SCA methods for user."""
        devices = self.auth_repo.get_registered_devices(user_identity_id)
        
        methods = []
        for device in devices:
            if device.passcode_enabled:
                methods.append("passcode")
            if device.biometric_enabled:
                methods.append("biometric")
        
        # Deduplicate
        return list(set(methods))

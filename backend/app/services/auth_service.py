"""
Authentication service implementing sign-in and session management.
Requirement: FR-AUTH-003, FR-AUTH-006
"""
import hashlib
import secrets
import uuid
from datetime import UTC, datetime, timedelta

from fastapi import HTTPException, status
from sqlalchemy.orm import Session

from app.adapters.ciam_sandbox_adapter import CIAMSandboxAdapter
from app.adapters.entitlement_sandbox_adapter import EntitlementSandboxAdapter
from app.config import settings
from app.models.customer_profile_ref import CustomerProfileRef
from app.repositories.auth_repository import AuthRepository
from app.schemas.auth_schemas import (
    LoginRequest,
    LoginResponse,
    SessionResponse,
    UserSummary,
)


class AuthService:
    """Service for authentication and session operations."""
    
    def __init__(
        self,
        db: Session,
        auth_repo: AuthRepository | None = None,
        ciam_adapter: CIAMSandboxAdapter | None = None,
        entitlement_adapter: EntitlementSandboxAdapter | None = None
    ):
        self.db = db
        self.auth_repo = auth_repo or AuthRepository(db)
        self.ciam_adapter = ciam_adapter or CIAMSandboxAdapter()
        self.entitlement_adapter = entitlement_adapter or EntitlementSandboxAdapter(db)
    
    def login(
        self,
        request: LoginRequest,
        client_address: str,
        correlation_id: str
    ) -> LoginResponse:
        """
        Authenticate user with passcode and create session.
        
        Steps per HLD 4.1:
        1. Check device is registered and active
        2. Verify passcode via CIAM adapter
        3. Create server-side session
        4. Record authentication event
        5. Record audit event
        
        Args:
            request: Login request with device_identifier, mobile_platform, passcode
            client_address: Client IP address for rate limiting
            correlation_id: Request correlation ID
        
        Returns:
            LoginResponse with bearer token and session details
        
        Raises:
            HTTPException: 401 for all failure cases with generic message
            HTTPException: 429 if rate limit exceeded
        """
        # Hash device identifier for lookup
        device_identifier_hash = self.auth_repo.hash_device_identifier(request.device_identifier)
        client_address_hash = self.auth_repo.hash_client_address(client_address)
        
        # Check rate limiting BEFORE device lookup
        if settings.rate_limit_enabled:
            # Check per-address limit
            address_attempts = self.auth_repo.count_recent_auth_attempts_by_address(
                client_address_hash,
                settings.rate_limit_login_per_address_window_seconds
            )
            if address_attempts >= settings.rate_limit_login_per_address_max_attempts:
                raise HTTPException(
                    status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                    detail="Too many sign-in attempts. Please try again later.",
                    headers={"Retry-After": str(settings.rate_limit_login_per_address_window_seconds)}
                )
        
        # Step 1: Get active device registration
        device = self.auth_repo.get_device_by_identifier_hash(
            device_identifier_hash,
            request.mobile_platform
        )
        
        if not device:
            # E-01 rejects unregistered device BEFORE passcode check
            self._record_failed_auth(
                None,
                None,
                client_address_hash,
                "unregistered_device",
                correlation_id
            )
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="We couldn't sign you in. Check your details and try again."
            )
        
        # Get customer profile
        customer = self.auth_repo.get_customer_by_id(device.customer_profile_ref_id)
        if not customer or not customer.is_active:
            self._record_failed_auth(
                device.customer_profile_ref_id,
                device.id,
                client_address_hash,
                "inactive_profile",
                correlation_id
            )
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="We couldn't sign you in. Check your details and try again."
            )
        
        # Check per-customer rate limit
        if settings.rate_limit_enabled:
            customer_attempts = self.auth_repo.count_recent_auth_attempts_by_customer(
                customer.id,
                settings.rate_limit_login_per_customer_window_seconds
            )
            if customer_attempts >= settings.rate_limit_login_per_customer_max_attempts:
                self._record_failed_auth(
                    customer.id,
                    device.id,
                    client_address_hash,
                    "rate_limited",
                    correlation_id
                )
                raise HTTPException(
                    status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                    detail="Too many sign-in attempts. Please try again later.",
                    headers={"Retry-After": str(settings.rate_limit_login_per_customer_window_seconds)}
                )
        
        # Step 2: Verify passcode via CIAM adapter
        credential = self.auth_repo.get_sandbox_credential(customer.id)
        if not credential:
            self._record_failed_auth(
                customer.id,
                device.id,
                client_address_hash,
                "no_credential",
                correlation_id
            )
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="We couldn't sign you in. Check your details and try again."
            )
        
        if not self.ciam_adapter.verify_passcode(request.passcode, credential.passcode_hash):
            self._record_failed_auth(
                customer.id,
                device.id,
                client_address_hash,
                "wrong_passcode",
                correlation_id
            )
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="We couldn't sign you in. Check your details and try again."
            )
        
        # Step 3: Create server-side session
        access_token = self._generate_token()
        token_hash = self._hash_token(access_token)
        issued_at = datetime.now(UTC)
        expires_at = issued_at + timedelta(minutes=settings.jwt_access_token_expire_minutes)
        
        session = self.auth_repo.create_session(
            customer_id=customer.id,
            device_id=device.id,
            token_hash=token_hash,
            issued_at=issued_at,
            expires_at=expires_at,
            correlation_id=correlation_id
        )
        
        # Step 4: Record successful authentication event
        self.auth_repo.record_authentication_event(
            customer_id=customer.id,
            device_id=device.id,
            client_address_hash=client_address_hash,
            authentication_type="passcode",
            outcome="success",
            failure_category=None,
            correlation_id=correlation_id
        )
        
        # Commit transaction
        self.db.commit()
        
        # Return login response
        return LoginResponse(
            access_token=access_token,
            token_type="Bearer",
            expires_in=settings.jwt_access_token_expire_minutes * 60,
            expires_at=expires_at,
            inactivity_timeout_seconds=settings.jwt_inactivity_timeout_minutes * 60,
            session_id=str(session.id),
            user=UserSummary(
                id=str(customer.id),
                display_name=customer.display_name,
                profile_type="personal"
            )
        )
    
    def validate_session(
        self,
        token: str,
        correlation_id: str
    ) -> SessionResponse:
        """
        Validate session and extend last_activity_at.
        
        Args:
            token: Bearer token from Authorization header
            correlation_id: Request correlation ID
        
        Returns:
            SessionResponse with session details
        
        Raises:
            HTTPException: 401 if session invalid, expired, or revoked
        """
        token_hash = self._hash_token(token)
        session = self.auth_repo.get_session_by_token_hash(token_hash)
        
        if not session:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid or expired session"
            )
        
        # Check if revoked
        if session.revoked_at is not None:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Session has been revoked"
            )
        
        now = datetime.now(UTC)
        
        # Check absolute expiry (ensure timezone-aware comparison)
        expires_at = session.expires_at
        if expires_at.tzinfo is None:
            expires_at = expires_at.replace(tzinfo=UTC)
        if now >= expires_at:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Session has expired"
            )
        
        # Check inactivity timeout
        # Ensure timezone-aware comparison
        last_activity = session.last_activity_at
        if last_activity.tzinfo is None:
            last_activity = last_activity.replace(tzinfo=UTC)
        inactivity_limit = last_activity + timedelta(minutes=settings.jwt_inactivity_timeout_minutes)
        if now >= inactivity_limit:
            self.auth_repo.revoke_session(session, "inactivity")
            self.db.commit()
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Session expired due to inactivity"
            )
        
        # Get customer for user summary
        customer = self.auth_repo.get_customer_by_id(session.customer_profile_ref_id)
        if not customer or not customer.is_active:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Customer profile not found or inactive"
            )
        
        # Update last activity (E-02 extends last_activity_at)
        self.auth_repo.update_session_activity(session)
        self.db.commit()
        
        # Calculate inactivity expiry (ensure timezone-aware)
        last_activity = session.last_activity_at
        if last_activity.tzinfo is None:
            last_activity = last_activity.replace(tzinfo=UTC)
        inactivity_expires_at = last_activity + timedelta(minutes=settings.jwt_inactivity_timeout_minutes)
        
        return SessionResponse(
            authenticated=True,
            session_id=str(session.id),
            issued_at=session.issued_at,
            expires_at=session.expires_at,
            last_activity_at=session.last_activity_at,
            inactivity_expires_at=inactivity_expires_at,
            user=UserSummary(
                id=str(customer.id),
                display_name=customer.display_name,
                profile_type="personal"
            )
        )
    
    def logout(
        self,
        token: str,
        correlation_id: str
    ) -> None:
        """
        End session by revoking token.
        
        Args:
            token: Bearer token from Authorization header
            correlation_id: Request correlation ID
        
        Raises:
            HTTPException: 401 if session not found or already revoked
        """
        token_hash = self._hash_token(token)
        session = self.auth_repo.get_session_by_token_hash(token_hash)
        
        if not session:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Session not found"
            )
        
        # Check if already revoked
        if session.revoked_at is not None:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Session already revoked"
            )
        
        # E-03 sets revoked_at
        self.auth_repo.revoke_session(session, "logout")
        self.db.commit()
    
    def get_current_user(self, token: str) -> CustomerProfileRef:
        """
        Get current user from token for dependency injection.
        
        Args:
            token: Bearer token
        
        Returns:
            CustomerProfileRef for the authenticated user
        
        Raises:
            HTTPException: 401 if session invalid
        """
        token_hash = self._hash_token(token)
        session = self.auth_repo.get_session_by_token_hash(token_hash)
        
        if not session or session.revoked_at is not None:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid or expired session"
            )
        
        # Check expiry and inactivity
        now = datetime.now(UTC)
        expires_at = session.expires_at
        if expires_at.tzinfo is None:
            expires_at = expires_at.replace(tzinfo=UTC)
        if now >= expires_at:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Session has expired"
            )
        
        last_activity = session.last_activity_at
        if last_activity.tzinfo is None:
            last_activity = last_activity.replace(tzinfo=UTC)
        inactivity_limit = last_activity + timedelta(minutes=settings.jwt_inactivity_timeout_minutes)
        if now >= inactivity_limit:
            self.auth_repo.revoke_session(session, "inactivity")
            self.db.commit()
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Session expired due to inactivity"
            )
        
        customer = self.auth_repo.get_customer_by_id(session.customer_profile_ref_id)
        if not customer or not customer.is_active:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Customer profile not found or inactive"
            )
        
        return customer
    
    def _record_failed_auth(
        self,
        customer_id: uuid.UUID | None,
        device_id: uuid.UUID | None,
        client_address_hash: str,
        failure_category: str,
        correlation_id: str
    ) -> None:
        """Record a failed authentication attempt."""
        # Authentication events allow NULL foreign keys when customer/device not resolved
        self.auth_repo.record_authentication_event(
            customer_id=customer_id,
            device_id=device_id,
            client_address_hash=client_address_hash,
            authentication_type="passcode",
            outcome="failed",
            failure_category=failure_category,
            correlation_id=correlation_id
        )
        self.db.commit()
    
    @staticmethod
    def _generate_token() -> str:
        """Generate a secure random token."""
        return secrets.token_urlsafe(32)
    
    @staticmethod
    def _hash_token(token: str) -> str:
        """Hash token with SHA-256."""
        return hashlib.sha256(token.encode('utf-8')).hexdigest()

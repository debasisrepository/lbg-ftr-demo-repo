"""
Authentication repository for session and credential data access.
Requirement: FR-AUTH-003, FR-AUTH-006
"""
import hashlib
import uuid
from datetime import UTC, datetime

from sqlalchemy import and_, select
from sqlalchemy.orm import Session

from app.models.authentication_event import AuthenticationEvent
from app.models.customer_profile_ref import CustomerProfileRef
from app.models.device_registration import DeviceRegistration
from app.models.sandbox_credential import SandboxCredential
from app.models.user_session import UserSession


class AuthRepository:
    """Repository for authentication and session operations."""
    
    def __init__(self, db: Session):
        self.db = db
    
    def get_device_by_identifier_hash(self, device_identifier_hash: str, mobile_platform: str) -> DeviceRegistration | None:
        """Get active device registration by identifier hash and platform."""
        stmt = select(DeviceRegistration).where(
            and_(
                DeviceRegistration.device_identifier_hash == device_identifier_hash,
                DeviceRegistration.mobile_platform == mobile_platform,
                DeviceRegistration.registration_status == "active"
            )
        )
        return self.db.execute(stmt).scalar_one_or_none()
    
    def get_customer_by_id(self, customer_id: uuid.UUID) -> CustomerProfileRef | None:
        """Get customer profile by ID."""
        stmt = select(CustomerProfileRef).where(
            and_(
                CustomerProfileRef.id == customer_id,
                CustomerProfileRef.is_active == True
            )
        )
        return self.db.execute(stmt).scalar_one_or_none()
    
    def get_sandbox_credential(self, customer_id: uuid.UUID) -> SandboxCredential | None:
        """Get sandbox credential for a customer."""
        stmt = select(SandboxCredential).where(
            SandboxCredential.customer_profile_ref_id == customer_id
        )
        return self.db.execute(stmt).scalar_one_or_none()
    
    def create_session(
        self,
        customer_id: uuid.UUID,
        device_id: uuid.UUID,
        token_hash: str,
        issued_at: datetime,
        expires_at: datetime,
        correlation_id: str
    ) -> UserSession:
        """Create a new user session."""
        session = UserSession(
            id=uuid.uuid4(),
            customer_profile_ref_id=customer_id,
            device_registration_id=device_id,
            token_hash=token_hash,
            issued_at=issued_at,
            expires_at=expires_at,
            last_activity_at=issued_at,
            correlation_id=correlation_id
        )
        self.db.add(session)
        self.db.flush()
        return session
    
    def get_session_by_token_hash(self, token_hash: str) -> UserSession | None:
        """Get session by token hash."""
        stmt = select(UserSession).where(
            UserSession.token_hash == token_hash
        )
        return self.db.execute(stmt).scalar_one_or_none()
    
    def update_session_activity(self, session: UserSession) -> None:
        """Update last activity time for a session."""
        session.updated_at = datetime.now(UTC)
        session.last_activity_at = datetime.now(UTC)
        self.db.flush()
    
    def revoke_session(self, session: UserSession, reason: str) -> None:
        """Revoke a session."""
        session.revoked_at = datetime.now(UTC)
        session.revocation_reason = reason
        session.updated_at = datetime.now(UTC)
        self.db.flush()
    
    def record_authentication_event(
        self,
        customer_id: uuid.UUID | None,
        device_id: uuid.UUID | None,
        client_address_hash: str,
        authentication_type: str,
        outcome: str,
        failure_category: str | None,
        correlation_id: str,
        ciam_transaction_reference: str | None = None
    ) -> AuthenticationEvent:
        """Record an authentication event."""
        event = AuthenticationEvent(
            id=uuid.uuid4(),
            customer_profile_ref_id=customer_id,
            device_registration_id=device_id,
            client_address_hash=client_address_hash,
            authentication_type=authentication_type,
            outcome=outcome,
            failure_category=failure_category,
            ciam_transaction_reference=ciam_transaction_reference,
            correlation_id=correlation_id,
            occurred_at=datetime.now(UTC)
        )
        self.db.add(event)
        self.db.flush()
        return event
    
    def count_recent_auth_attempts_by_address(
        self,
        client_address_hash: str,
        window_seconds: int
    ) -> int:
        """Count authentication attempts from a client address in the time window."""
        cutoff = datetime.now(UTC).timestamp() - window_seconds
        cutoff_dt = datetime.fromtimestamp(cutoff, tz=UTC)
        
        stmt = select(AuthenticationEvent).where(
            and_(
                AuthenticationEvent.client_address_hash == client_address_hash,
                AuthenticationEvent.occurred_at >= cutoff_dt,
                AuthenticationEvent.outcome.in_(["failed", "denied", "rate_limited"])
            )
        )
        result = self.db.execute(stmt)
        return len(result.scalars().all())
    
    def count_recent_auth_attempts_by_customer(
        self,
        customer_id: uuid.UUID,
        window_seconds: int
    ) -> int:
        """Count authentication attempts for a customer in the time window."""
        cutoff = datetime.now(UTC).timestamp() - window_seconds
        cutoff_dt = datetime.fromtimestamp(cutoff, tz=UTC)
        
        stmt = select(AuthenticationEvent).where(
            and_(
                AuthenticationEvent.customer_profile_ref_id == customer_id,
                AuthenticationEvent.occurred_at >= cutoff_dt,
                AuthenticationEvent.outcome.in_(["failed", "denied", "rate_limited"])
            )
        )
        result = self.db.execute(stmt)
        return len(result.scalars().all())
    
    @staticmethod
    def hash_device_identifier(device_identifier: str) -> str:
        """Hash device identifier with SHA-256."""
        return hashlib.sha256(device_identifier.encode('utf-8')).hexdigest()
    
    @staticmethod
    def hash_client_address(client_address: str) -> str:
        """Hash client IP address with SHA-256."""
        return hashlib.sha256(client_address.encode('utf-8')).hexdigest()

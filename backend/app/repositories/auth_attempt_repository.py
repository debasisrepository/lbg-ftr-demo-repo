"""Auth attempt repository for tracking authentication attempts"""
import uuid
from datetime import UTC, datetime, timedelta

from sqlalchemy import select
from sqlalchemy.orm import Session

from ..models.session import AuthAttempt


class AuthAttemptRepository:
    """Auth attempt data access"""

    def __init__(self, db: Session):
        self.db = db

    def create(
        self,
        customer_id: uuid.UUID | None,
        device_id: uuid.UUID | None,
        identifier_hash: str,
        attempt_type: str,
        outcome: str,
        client_ip_hash: str | None,
        correlation_id: str,
        occurred_at: datetime
    ) -> AuthAttempt:
        """Record an authentication attempt"""
        attempt = AuthAttempt(
            auth_attempt_id=uuid.uuid4(),
            customer_id=customer_id,
            device_id=device_id,
            identifier_hash=identifier_hash,
            attempt_type=attempt_type,
            outcome=outcome,
            client_ip_hash=client_ip_hash,
            correlation_id=correlation_id,
            occurred_at=occurred_at
        )
        self.db.add(attempt)
        self.db.flush()
        return attempt

    def count_recent_failures_by_identifier(
        self,
        identifier_hash: str,
        attempt_type: str,
        window_minutes: int = 15
    ) -> int:
        """Count recent failures for an identifier within time window"""
        cutoff = datetime.now(UTC) - timedelta(minutes=window_minutes)
        stmt = select(AuthAttempt).where(
            AuthAttempt.identifier_hash == identifier_hash,
            AuthAttempt.attempt_type == attempt_type,
            AuthAttempt.outcome.in_(['failure', 'rate_limited']),
            AuthAttempt.occurred_at >= cutoff
        )
        result = self.db.execute(stmt)
        attempts = result.scalars().all()
        return len(attempts)

    def count_recent_attempts_by_ip(
        self,
        client_ip_hash: str,
        window_minutes: int = 15
    ) -> int:
        """Count recent attempts from an IP within time window"""
        cutoff = datetime.now(UTC) - timedelta(minutes=window_minutes)
        stmt = select(AuthAttempt).where(
            AuthAttempt.client_ip_hash == client_ip_hash,
            AuthAttempt.occurred_at >= cutoff
        )
        result = self.db.execute(stmt)
        attempts = result.scalars().all()
        return len(attempts)

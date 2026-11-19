"""Step-up challenge repository"""
import uuid
from datetime import UTC, datetime

from sqlalchemy import select
from sqlalchemy.orm import Session

from ..models.session import StepUpChallenge


class StepUpRepository:
    """Step-up challenge data access"""

    def __init__(self, db: Session):
        self.db = db

    def get_by_reference(self, challenge_reference: str) -> StepUpChallenge | None:
        """Get challenge by reference"""
        stmt = select(StepUpChallenge).where(
            StepUpChallenge.challenge_reference == challenge_reference
        )
        result = self.db.execute(stmt)
        return result.scalar_one_or_none()

    def create(
        self,
        customer_id: uuid.UUID,
        device_id: uuid.UUID | None,
        session_id: uuid.UUID | None,
        purpose: str,
        method: str,
        challenge_reference: str,
        issued_at: datetime,
        expires_at: datetime,
        correlation_id: str
    ) -> StepUpChallenge:
        """Create a step-up challenge"""
        challenge = StepUpChallenge(
            step_up_challenge_id=uuid.uuid4(),
            customer_id=customer_id,
            device_id=device_id,
            session_id=session_id,
            purpose=purpose,
            method=method,
            challenge_reference=challenge_reference,
            result='issued',
            attempt_count=0,
            issued_at=issued_at,
            expires_at=expires_at,
            correlation_id=correlation_id
        )
        self.db.add(challenge)
        self.db.flush()
        return challenge

    def increment_attempt_count(self, challenge: StepUpChallenge) -> None:
        """Increment challenge attempt count"""
        challenge.attempt_count += 1
        challenge.updated_at = datetime.now(UTC)
        self.db.flush()

    def mark_passed(self, challenge: StepUpChallenge) -> None:
        """Mark challenge as passed"""
        now = datetime.now(UTC)
        challenge.result = 'passed'
        challenge.completed_at = now
        challenge.updated_at = now
        self.db.flush()

    def mark_failed(self, challenge: StepUpChallenge) -> None:
        """Mark challenge as failed"""
        now = datetime.now(UTC)
        challenge.result = 'failed'
        challenge.completed_at = now
        challenge.updated_at = now
        self.db.flush()

    def mark_expired(self, challenge: StepUpChallenge) -> None:
        """Mark challenge as expired"""
        challenge.result = 'expired'
        challenge.updated_at = datetime.now(UTC)
        self.db.flush()

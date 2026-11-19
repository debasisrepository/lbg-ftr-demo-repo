from datetime import datetime, timezone
from sqlalchemy.orm import Session
from app.models.sca import StepUpChallenge
from app.common.enums import ChallengeType, ChallengeMethod, ChallengeStatus


class SCARepository:
    """Repository for SCA-related database operations."""

    def __init__(self, db: Session):
        self.db = db

    def create_challenge(
        self,
        auth_session_id: int,
        challenge_type: str,
        method: str,
        max_attempts: int,
        device_id: str | None = None,
        challenge_expires_at: datetime | None = None
    ) -> StepUpChallenge:
        """Create a new step-up challenge."""
        now = datetime.now(timezone.utc)
        challenge = StepUpChallenge(
            auth_session_id=auth_session_id,
            payment_instruction_id=None,
            challenge_type=challenge_type,
            method=method,
            status=ChallengeStatus.PENDING.value,
            device_id=device_id,
            attempts_used=0,
            max_attempts=max_attempts,
            dynamic_link_hash=None,
            challenge_expires_at=challenge_expires_at,
            verified_at=None,
            created_at=now,
            updated_at=now
        )
        self.db.add(challenge)
        self.db.commit()
        self.db.refresh(challenge)
        return challenge

    def get_challenge_by_id(self, challenge_id: int) -> StepUpChallenge | None:
        """Get challenge by ID."""
        return self.db.query(StepUpChallenge).filter(
            StepUpChallenge.id == challenge_id
        ).first()

    def get_challenge_by_session(
        self,
        auth_session_id: int,
        challenge_type: str
    ) -> StepUpChallenge | None:
        """Get latest challenge for a session and type."""
        return self.db.query(StepUpChallenge).filter(
            StepUpChallenge.auth_session_id == auth_session_id,
            StepUpChallenge.challenge_type == challenge_type
        ).order_by(StepUpChallenge.created_at.desc()).first()

    def increment_attempts(self, challenge_id: int) -> StepUpChallenge | None:
        """Increment challenge attempt counter."""
        challenge = self.db.query(StepUpChallenge).filter(
            StepUpChallenge.id == challenge_id
        ).first()
        if challenge:
            challenge.attempts_used += 1
            challenge.updated_at = datetime.now(timezone.utc)
            
            if challenge.attempts_used >= challenge.max_attempts:
                challenge.status = ChallengeStatus.LOCKED.value
                
            self.db.commit()
            self.db.refresh(challenge)
        return challenge

    def mark_verified(self, challenge_id: int) -> None:
        """Mark challenge as verified."""
        challenge = self.db.query(StepUpChallenge).filter(
            StepUpChallenge.id == challenge_id
        ).first()
        if challenge:
            challenge.status = ChallengeStatus.VERIFIED.value
            challenge.verified_at = datetime.now(timezone.utc)
            challenge.updated_at = datetime.now(timezone.utc)
            self.db.commit()

    def mark_failed(self, challenge_id: int) -> None:
        """Mark challenge as failed."""
        challenge = self.db.query(StepUpChallenge).filter(
            StepUpChallenge.id == challenge_id
        ).first()
        if challenge:
            challenge.status = ChallengeStatus.FAILED.value
            challenge.updated_at = datetime.now(timezone.utc)
            self.db.commit()

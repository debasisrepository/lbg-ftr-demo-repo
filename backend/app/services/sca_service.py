from datetime import datetime, timedelta, timezone
from sqlalchemy.orm import Session
from app.repositories.sca_repository import SCARepository
from app.repositories.auth_repository import AuthRepository
from app.services.audit_service import AuditService
from app.services.telemetry_service import TelemetryService
from app.adapters.sca_provider_adapter import SCAProviderAdapter
from app.common.enums import ChallengeType, ChallengeMethod, ChallengeStatus, JourneyOutcomeCode
from app.common.errors import ValidationError


class SCAService:
    """Service for step-up authentication (SCA) operations."""

    def __init__(self, db: Session, correlation_id: str):
        self.db = db
        self.correlation_id = correlation_id
        self.sca_repo = SCARepository(db)
        self.auth_repo = AuthRepository(db)
        self.audit_service = AuditService(db)
        self.telemetry_service = TelemetryService(db)
        self.sca_adapter = SCAProviderAdapter()

    def create_login_step_up_challenge(self, auth_session_id: int, device_id: str | None = None) -> int:
        """
        Create a login step-up challenge.
        
        Returns challenge_id.
        """
        challenge_expires_at = datetime.now(timezone.utc) + timedelta(minutes=10)
        
        challenge = self.sca_repo.create_challenge(
            auth_session_id=auth_session_id,
            challenge_type=ChallengeType.LOGIN_STEP_UP.value,
            method=ChallengeMethod.PASSCODE.value,  # Default to passcode
            max_attempts=3,
            device_id=device_id,
            challenge_expires_at=challenge_expires_at
        )
        
        return challenge.id

    async def verify_step_up(
        self,
        session_id: int,
        method: str,
        passcode: str | None = None,
        biometric_assertion: str | None = None,
        device_id: str | None = None
    ) -> dict:
        """
        Verify step-up authentication attempt.
        
        Returns dict with verification result.
        """
        # Get session
        session = self.auth_repo.get_session_by_id(session_id)
        if not session:
            raise ValidationError("Invalid session")

        # Get or create challenge
        challenge = self.sca_repo.get_challenge_by_session(
            auth_session_id=session_id,
            challenge_type=ChallengeType.LOGIN_STEP_UP.value
        )
        
        if not challenge:
            # Create challenge if it doesn't exist
            challenge_id = self.create_login_step_up_challenge(session_id, device_id)
            challenge = self.sca_repo.get_challenge_by_session(
                auth_session_id=session_id,
                challenge_type=ChallengeType.LOGIN_STEP_UP.value
            )

        # Check if already locked
        if challenge.status == ChallengeStatus.LOCKED.value:
            self.telemetry_service.emit_prove_identity_event(
                correlation_id=self.correlation_id,
                auth_session_id=session_id,
                outcome_code=JourneyOutcomeCode.BLOCKED.value,
                failure_reason="passcode_locked"
            )
            return {
                "status": "locked",
                "session_id": session_id,
                "step_up_verified": False,
                "remaining_attempts": 0,
                "next_route": "/login",
                "available_methods": self._get_fallback_methods(session.user_identity_id)
            }

        # Check if expired
        if challenge.challenge_expires_at:
            # Make both datetimes timezone-aware for comparison
            now_utc = datetime.now(timezone.utc)
            expires_at = challenge.challenge_expires_at
            if expires_at.tzinfo is None:
                expires_at = expires_at.replace(tzinfo=timezone.utc)
            
            if expires_at < now_utc:
                self.sca_repo.mark_failed(challenge.id)
                raise ValidationError("Challenge expired")

        # Verify based on method
        verified = False
        if method == "passcode":
            if not passcode:
                raise ValidationError("Passcode required")
            verified = await self.sca_adapter.verify_passcode(
                user_identity_id=session.user_identity_id,
                device_id=device_id or "default",
                passcode=passcode
            )
        elif method == "biometric":
            if not biometric_assertion:
                raise ValidationError("Biometric assertion required")
            verified = await self.sca_adapter.verify_biometric(
                user_identity_id=session.user_identity_id,
                device_id=device_id or "default",
                biometric_assertion=biometric_assertion
            )
        else:
            raise ValidationError("Invalid verification method")

        if verified:
            # Success
            self.sca_repo.mark_verified(challenge.id)
            self.audit_service.log_step_up_verified(
                correlation_id=self.correlation_id,
                auth_session_id=session_id,
                user_identity_id=session.user_identity_id,
                challenge_id=challenge.id,
                method=method
            )
            self.telemetry_service.emit_prove_identity_event(
                correlation_id=self.correlation_id,
                auth_session_id=session_id,
                outcome_code=JourneyOutcomeCode.SUCCESS.value
            )
            
            return {
                "status": "verified",
                "session_id": session_id,
                "step_up_verified": True,
                "remaining_attempts": None,
                "next_route": "/accounts",
                "available_methods": []
            }
        else:
            # Failed attempt
            challenge = self.sca_repo.increment_attempts(challenge.id)
            remaining = challenge.max_attempts - challenge.attempts_used
            
            if challenge.status == ChallengeStatus.LOCKED.value:
                # Locked after max attempts
                self.audit_service.log_step_up_locked(
                    correlation_id=self.correlation_id,
                    auth_session_id=session_id,
                    user_identity_id=session.user_identity_id,
                    challenge_id=challenge.id,
                    attempts_used=challenge.attempts_used
                )
                self.telemetry_service.emit_prove_identity_event(
                    correlation_id=self.correlation_id,
                    auth_session_id=session_id,
                    outcome_code=JourneyOutcomeCode.BLOCKED.value,
                    failure_reason="max_attempts_exceeded"
                )
                
                return {
                    "status": "locked",
                    "session_id": session_id,
                    "step_up_verified": False,
                    "remaining_attempts": 0,
                    "next_route": "/login",
                    "available_methods": self._get_fallback_methods(session.user_identity_id)
                }
            else:
                # Failed but not locked yet
                self.telemetry_service.emit_prove_identity_event(
                    correlation_id=self.correlation_id,
                    auth_session_id=session_id,
                    outcome_code=JourneyOutcomeCode.FAILURE.value,
                    failure_reason="invalid_credentials"
                )
                
                return {
                    "status": "failed",
                    "session_id": session_id,
                    "step_up_verified": False,
                    "remaining_attempts": remaining,
                    "next_route": "/step-up",
                    "available_methods": [method]
                }

    def _get_fallback_methods(self, user_identity_id: int) -> list[str]:
        """Get fallback authentication methods (password)."""
        return ["password"]

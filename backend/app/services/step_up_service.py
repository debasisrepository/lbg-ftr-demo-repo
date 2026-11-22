"""Step-up authentication service"""
import uuid
from datetime import UTC, datetime, timedelta

from sqlalchemy.orm import Session

from ..adapters.ciam_adapter import CiamAdapter, get_ciam_adapter
from ..config import settings
from ..core.errors import AuthenticationError, ValidationError
from ..core.security import generate_hmac_digest
from ..repositories.device_repository import DeviceRepository
from ..repositories.session_repository import SessionRepository
from ..repositories.step_up_repository import StepUpRepository
from ..schemas.auth_schemas import (
    StepUpChallengeRequest,
    StepUpChallengeResponse,
    VerifyStepUpRequest,
    VerifyStepUpResponse,
)


class StepUpService:
    """Step-up authentication for sensitive actions"""

    def __init__(self, db: Session):
        self.db = db
        self.step_up_repo = StepUpRepository(db)
        self.session_repo = SessionRepository(db)
        self.device_repo = DeviceRepository(db)
        self.ciam_adapter: CiamAdapter = get_ciam_adapter()

    def create_challenge(
        self,
        session_id: uuid.UUID,
        request: StepUpChallengeRequest,
        correlation_id: str
    ) -> StepUpChallengeResponse:
        """Create a step-up challenge for a sensitive action"""
        session = self.session_repo.get_by_id(session_id)

        if not session or session.ended_at is not None:
            raise AuthenticationError("Invalid or ended session")

        if session.auth_level not in ['proven', 'step_up']:
            raise AuthenticationError("Session must be proven before step-up")

        # Generate challenge reference with HMAC binding (LLD section 4.2.1)
        now = datetime.now(UTC)
        expires_at = now + timedelta(minutes=5)  # 5 minute step-up window

        # Bind challenge to purpose and context
        context_str = str(request.context) if request.context else ""
        challenge_reference = generate_hmac_digest(
            settings.secret_key,
            str(session_id),
            request.purpose,
            context_str,
            str(int(now.timestamp()))
        )

        # Determine method based on device capabilities
        method = 'passcode'  # Default
        if session.device_id:
            device = self.device_repo.get_by_id(session.device_id)
            if device and device.biometric_enabled:
                method = 'biometric_attestation'

        self.step_up_repo.create(
            customer_id=session.customer_id,
            device_id=session.device_id,
            session_id=session_id,
            purpose=request.purpose,
            method=method,
            challenge_reference=challenge_reference,
            issued_at=now,
            expires_at=expires_at,
            correlation_id=correlation_id
        )

        self.db.commit()

        return StepUpChallengeResponse(
            challenge_reference=challenge_reference,
            method=method,
            expires_at=expires_at
        )

    def verify_challenge(
        self,
        challenge_reference: str,
        request: VerifyStepUpRequest,
        correlation_id: str
    ) -> VerifyStepUpResponse:
        """Verify a step-up challenge"""
        challenge = self.step_up_repo.get_by_reference(challenge_reference)

        if not challenge:
            raise ValidationError("Invalid challenge reference")

        if challenge.result != 'issued':
            raise ValidationError("Challenge already completed or expired")

        # Check expiry (ensure timezone-aware comparison)
        now = datetime.now(UTC)
        challenge_expires = challenge.expires_at if challenge.expires_at.tzinfo else challenge.expires_at.replace(tzinfo=UTC)
        if now > challenge_expires:
            self.step_up_repo.mark_expired(challenge)
            self.db.commit()
            raise AuthenticationError("Challenge has expired")

        # Increment attempt count
        self.step_up_repo.increment_attempt_count(challenge)

        # Verify proof based on method
        proof_success = False

        if request.proof_type == 'passcode':
            if not request.proof_value:
                raise ValidationError("Passcode required")

            # Verify with CIAM
            proof_success = self.ciam_adapter.verify_passcode(
                challenge.customer_id,
                challenge.device_id or uuid.UUID(int=0),
                request.proof_value
            )

        elif request.proof_type == 'biometric':
            if not request.proof_value or not request.device_id:
                raise ValidationError("Biometric attestation and device ID required")

            device_id_uuid = uuid.UUID(request.device_id)
            proof_success = self.ciam_adapter.verify_biometric(
                challenge.customer_id,
                device_id_uuid,
                request.proof_value
            )
        else:
            raise ValidationError(f"Unsupported proof type: {request.proof_type}")

        if proof_success:
            self.step_up_repo.mark_passed(challenge)

            # Upgrade session to step_up auth level if it has a session
            if challenge.session_id:
                session = self.session_repo.get_by_id(challenge.session_id)
                if session:
                    self.session_repo.update_auth_level(session, 'step_up')
        else:
            self.step_up_repo.mark_failed(challenge)

        self.db.commit()

        if not proof_success:
            raise AuthenticationError("Step-up verification failed")

        return VerifyStepUpResponse(
            result='passed',
            auth_level='step_up'
        )

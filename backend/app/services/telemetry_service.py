from sqlalchemy.orm import Session
from app.repositories.telemetry_repository import TelemetryRepository
from app.common.enums import JourneyStep, JourneyOutcomeCode


class TelemetryService:
    """Service for journey telemetry and observability."""

    def __init__(self, db: Session):
        self.telemetry_repo = TelemetryRepository(db)

    def emit_sign_in_event(
        self,
        correlation_id: str,
        auth_session_id: int | None,
        outcome_code: str,
        failure_reason: str | None = None,
        payload: dict | None = None
    ) -> None:
        """Emit sign-in journey event."""
        self.telemetry_repo.create_journey_event(
            correlation_id=correlation_id,
            auth_session_id=auth_session_id,
            profile_id=None,
            journey_step=JourneyStep.SIGN_IN.value,
            outcome_code=outcome_code,
            failure_reason=failure_reason,
            event_payload=payload
        )

    def emit_prove_identity_event(
        self,
        correlation_id: str,
        auth_session_id: int,
        outcome_code: str,
        failure_reason: str | None = None,
        payload: dict | None = None
    ) -> None:
        """Emit prove-identity journey event."""
        self.telemetry_repo.create_journey_event(
            correlation_id=correlation_id,
            auth_session_id=auth_session_id,
            profile_id=None,
            journey_step=JourneyStep.PROVE_IDENTITY.value,
            outcome_code=outcome_code,
            failure_reason=failure_reason,
            event_payload=payload
        )

    def emit_enter_approve_event(
        self,
        correlation_id: str,
        auth_session_id: int,
        profile_id: int,
        outcome_code: str,
        failure_reason: str | None = None,
        payload: dict | None = None
    ) -> None:
        """Emit enter-approve journey event."""
        self.telemetry_repo.create_journey_event(
            correlation_id=correlation_id,
            auth_session_id=auth_session_id,
            profile_id=profile_id,
            journey_step=JourneyStep.ENTER_APPROVE.value,
            outcome_code=outcome_code,
            failure_reason=failure_reason,
            event_payload=payload
        )

    def emit_payment_sent_event(
        self,
        correlation_id: str,
        auth_session_id: int,
        profile_id: int,
        outcome_code: str,
        failure_reason: str | None = None,
        payload: dict | None = None
    ) -> None:
        """Emit payment-sent journey event."""
        self.telemetry_repo.create_journey_event(
            correlation_id=correlation_id,
            auth_session_id=auth_session_id,
            profile_id=profile_id,
            journey_step=JourneyStep.PAYMENT_SENT.value,
            outcome_code=outcome_code,
            failure_reason=failure_reason,
            event_payload=payload
        )

from datetime import datetime, timezone
from sqlalchemy.orm import Session
from app.models.telemetry import JourneyEvent
import json


class TelemetryRepository:
    """Repository for telemetry database operations."""

    def __init__(self, db: Session):
        self.db = db

    def create_journey_event(
        self,
        correlation_id: str,
        auth_session_id: int | None,
        profile_id: int | None,
        journey_step: str,
        outcome_code: str,
        failure_reason: str | None = None,
        event_payload: dict | None = None
    ) -> JourneyEvent:
        """Create a new journey event."""
        now = datetime.now(timezone.utc)
        event = JourneyEvent(
            correlation_id=correlation_id,
            auth_session_id=auth_session_id,
            profile_id=profile_id,
            journey_step=journey_step,
            outcome_code=outcome_code,
            failure_reason=failure_reason,
            event_payload_json=json.dumps(event_payload) if event_payload else None,
            occurred_at=now,
            created_at=now
        )
        self.db.add(event)
        self.db.commit()
        self.db.refresh(event)
        return event

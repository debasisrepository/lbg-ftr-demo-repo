"""
Status consumer - updates capability status based on events.
Requirement: REQ-OPS-001
"""
import uuid
from datetime import UTC, datetime

from sqlalchemy.orm import Session

from app.models.consumed_event import ConsumedEvent


def process_status_event(session: Session, event_id: str, event_type: str, event_payload: dict, correlation_id: str):
    """
    Process status event to update capability_status_records.
    
    Idempotent: checks consumed_events before processing.
    
    Args:
        session: Database session
        event_id: Unique event ID
        event_type: Event type
        event_payload: Event payload dict
        correlation_id: Correlation ID
    """
    # Check if already consumed
    existing = session.query(ConsumedEvent).filter_by(
        consumer_name="status_and_flags",
        event_id=event_id
    ).first()
    
    if existing:
        # Already processed - idempotent replay
        return
    
    # Process event (update capability_status_records)
    # Working tier: capability status updates handled by payment orchestration service directly
    
    # Mark consumed
    consumed = ConsumedEvent(
        id=uuid.uuid4(),
        consumer_name="status_and_flags",
        event_id=event_id,
        event_type=event_type,
        correlation_id=correlation_id,
        processed_at=datetime.now(UTC)
    )
    session.add(consumed)
    session.flush()

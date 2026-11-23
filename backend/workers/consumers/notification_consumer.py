"""
Notification consumer - triggers notifications based on payment events.
Requirement: REQ-OPS-005 (deferred, seam only)
"""
import uuid
from datetime import UTC, datetime

from sqlalchemy.orm import Session

from app.models.consumed_event import ConsumedEvent


def process_notification_event(session: Session, event_id: str, event_type: str, event_payload: dict, correlation_id: str):
    """
    Process notification event.
    
    Idempotent: checks consumed_events before processing.
    Working tier: notification triggers not built, consumer seam only.
    
    Args:
        session: Database session
        event_id: Unique event ID
        event_type: Event type
        event_payload: Event payload dict
        correlation_id: Correlation ID
    """
    # Check if already consumed
    existing = session.query(ConsumedEvent).filter_by(
        consumer_name="notifications",
        event_id=event_id
    ).first()
    
    if existing:
        # Already processed - idempotent replay
        return
    
    # Process event (trigger notifications via APNs/FCM adapter)
    # Working tier: notification delivery not built, seam only
    
    # Mark consumed
    consumed = ConsumedEvent(
        id=uuid.uuid4(),
        consumer_name="notifications",
        event_id=event_id,
        event_type=event_type,
        correlation_id=correlation_id,
        processed_at=datetime.now(UTC)
    )
    session.add(consumed)
    session.flush()

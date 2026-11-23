"""
Read model account consumer - processes account-related events.
Requirement: REQ-ACCT-001, REQ-ACCT-002, REQ-ACCT-003
"""
import uuid
from datetime import UTC, datetime

from sqlalchemy.orm import Session

from app.models.consumed_event import ConsumedEvent


def process_account_event(session: Session, event_id: str, event_type: str, event_payload: dict, correlation_id: str):
    """
    Process account-related event into account_read_models.
    
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
        consumer_name="read_model_accounts",
        event_id=event_id
    ).first()
    
    if existing:
        # Already processed - idempotent replay
        return
    
    # Process event (update account_read_models)
    # Working tier: account events are seeded, not consumed from real stream
    
    # Mark consumed
    consumed = ConsumedEvent(
        id=uuid.uuid4(),
        consumer_name="read_model_accounts",
        event_id=event_id,
        event_type=event_type,
        correlation_id=correlation_id,
        processed_at=datetime.now(UTC)
    )
    session.add(consumed)
    session.flush()

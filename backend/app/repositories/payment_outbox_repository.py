"""PaymentOutboxRepository - manage payment outbox events."""
from datetime import UTC, datetime

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.payment_outbox_event import PaymentOutboxEvent


class PaymentOutboxRepository:
    """Repository for payment outbox event operations."""
    
    def __init__(self, db: Session):
        self.db = db
    
    def create(self, event: PaymentOutboxEvent) -> PaymentOutboxEvent:
        """Create a new outbox event."""
        self.db.add(event)
        self.db.flush()
        return event
    
    def get_pending_events(self, limit: int = 100) -> list[PaymentOutboxEvent]:
        """Get pending outbox events ready for publication."""
        now = datetime.now(UTC)
        stmt = select(PaymentOutboxEvent).where(
            PaymentOutboxEvent.publish_state.in_(['pending', 'retrying'])
        ).where(
            (PaymentOutboxEvent.next_attempt_at.is_(None)) | 
            (PaymentOutboxEvent.next_attempt_at <= now)
        ).order_by(
            PaymentOutboxEvent.created_at
        ).limit(limit)
        
        result = self.db.execute(stmt)
        return list(result.scalars().all())
    
    def mark_published(
        self,
        event: PaymentOutboxEvent,
        event_stream_reference: str | None = None
    ) -> PaymentOutboxEvent:
        """Mark an event as successfully published."""
        event.publish_state = "published"
        event.published_at = datetime.now(UTC)
        event.event_stream_reference = event_stream_reference
        event.updated_at = datetime.now(UTC)
        self.db.flush()
        return event
    
    def mark_failed(
        self,
        event: PaymentOutboxEvent,
        error_code: str,
        next_attempt_at: datetime | None = None
    ) -> PaymentOutboxEvent:
        """Mark an event as failed and schedule retry if applicable."""
        event.attempt_count += 1
        event.last_error_code = error_code
        event.next_attempt_at = next_attempt_at
        event.publish_state = "retrying" if next_attempt_at else "failed"
        event.updated_at = datetime.now(UTC)
        self.db.flush()
        return event

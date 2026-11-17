from sqlalchemy.orm import Session
from app.events.repository import EventRepository


class EventPublisher:
    def __init__(self, db: Session):
        self.db = db
        self.repo = EventRepository(db)

    def publish(
        self,
        event_type: str,
        idempotency_key: str,
        entity_type: str,
        entity_id: str,
        correlation_id: str,
        payload: dict | None = None,
    ):
        existing = self.repo.get_event_by_idempotency_key(idempotency_key)
        if existing:
            return existing

        event = self.repo.create_domain_event(
            event_type=event_type,
            idempotency_key=idempotency_key,
            entity_type=entity_type,
            entity_id=entity_id,
            correlation_id=correlation_id,
            payload=payload,
        )
        self.repo.create_outbox_entry(event.id)
        return event

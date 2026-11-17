from datetime import datetime, timedelta
from sqlalchemy import select, and_
from sqlalchemy.orm import Session
import uuid
from app.core.clock import Clock
from app.core.ids import IdGenerator
from app.events.models import DomainEvent, EventOutbox


class EventRepository:
    def __init__(self, db: Session):
        self.db = db

    def create_domain_event(
        self,
        event_type: str,
        idempotency_key: str,
        entity_type: str,
        entity_id: str,
        correlation_id: str,
        payload: dict | None = None,
    ) -> DomainEvent:
        event = DomainEvent(
            id=IdGenerator.uuid4(),
            event_type=event_type,
            idempotency_key=idempotency_key,
            entity_type=entity_type,
            entity_id=entity_id,
            payload=payload,
            correlation_id=correlation_id,
            occurred_at=Clock.utc_now(),
        )
        self.db.add(event)
        return event

    def get_event_by_idempotency_key(self, idempotency_key: str) -> DomainEvent | None:
        stmt = select(DomainEvent).where(DomainEvent.idempotency_key == idempotency_key)
        return self.db.execute(stmt).scalar_one_or_none()

    def create_outbox_entry(self, event_id: uuid.UUID, next_attempt_at: datetime | None = None) -> EventOutbox:
        if next_attempt_at is None:
            next_attempt_at = Clock.utc_now()
        outbox = EventOutbox(
            id=IdGenerator.uuid4(),
            event_id=event_id,
            status="pending",
            retry_count=0,
            next_attempt_at=next_attempt_at,
        )
        self.db.add(outbox)
        return outbox

    def get_pending_outbox_entries(self, limit: int = 100) -> list[EventOutbox]:
        now = Clock.utc_now()
        stmt = (
            select(EventOutbox)
            .where(
                and_(
                    EventOutbox.status == "pending",
                    EventOutbox.next_attempt_at <= now,
                )
            )
            .order_by(EventOutbox.next_attempt_at)
            .limit(limit)
        )
        return list(self.db.execute(stmt).scalars().all())

    def mark_outbox_published(self, outbox_id: uuid.UUID):
        stmt = select(EventOutbox).where(EventOutbox.id == outbox_id)
        outbox = self.db.execute(stmt).scalar_one_or_none()
        if outbox:
            outbox.status = "published"
            outbox.published_at = Clock.utc_now()

    def mark_outbox_failed(self, outbox_id: uuid.UUID, error: str):
        stmt = select(EventOutbox).where(EventOutbox.id == outbox_id)
        outbox = self.db.execute(stmt).scalar_one_or_none()
        if outbox:
            outbox.retry_count += 1
            outbox.last_error = error[:2000]
            if outbox.retry_count >= 5:
                outbox.status = "failed"
            else:
                delay_minutes = min(2 ** outbox.retry_count, 60)
                outbox.next_attempt_at = Clock.utc_now() + timedelta(minutes=delay_minutes)

    def get_event_by_id(self, event_id: uuid.UUID) -> DomainEvent | None:
        return self.db.get(DomainEvent, event_id)

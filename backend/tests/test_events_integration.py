import time
import uuid
from app.events.publisher import EventPublisher
from app.events.repository import EventRepository
from app.events.registry import get_event_registry
from app.events.dispatcher import OutboxDispatcher


def test_event_publication_creates_domain_event_and_outbox(db_session):
    publisher = EventPublisher(db_session)
    event = publisher.publish(
        event_type="CaseCaptured",
        idempotency_key="test-case-1",
        entity_type="case",
        entity_id="case-123",
        correlation_id="corr-1",
        payload={"case_id": str(uuid.uuid4()), "case_ref": "CP-2026-000001"},
    )
    db_session.commit()

    assert event.event_type == "CaseCaptured"
    assert event.idempotency_key == "test-case-1"

    repo = EventRepository(db_session)
    outbox_entries = repo.get_pending_outbox_entries()
    assert len(outbox_entries) == 1
    assert outbox_entries[0].event_id == event.id
    assert outbox_entries[0].status == "pending"


def test_event_publication_is_idempotent(db_session):
    publisher = EventPublisher(db_session)
    event1 = publisher.publish(
        event_type="CaseCaptured",
        idempotency_key="test-case-2",
        entity_type="case",
        entity_id="case-456",
        correlation_id="corr-2",
    )
    db_session.commit()

    event2 = publisher.publish(
        event_type="CaseCaptured",
        idempotency_key="test-case-2",
        entity_type="case",
        entity_id="case-456",
        correlation_id="corr-2",
    )
    db_session.commit()

    assert event1.id == event2.id


def test_outbox_dispatch_marks_published(db_session):
    publisher = EventPublisher(db_session)
    event = publisher.publish(
        event_type="CaseCaptured",
        idempotency_key="test-case-3",
        entity_type="case",
        entity_id="case-789",
        correlation_id="corr-3",
        payload={"case_id": str(uuid.uuid4()), "case_ref": "CP-2026-000002"},
    )
    db_session.commit()

    handler_called = []
    def test_handler(event_id, payload):
        handler_called.append((event_id, payload))

    registry = get_event_registry()
    registry.register("CaseCaptured", test_handler)

    dispatcher = OutboxDispatcher()
    dispatcher._dispatch_batch()

    repo = EventRepository(db_session)
    outbox_entries = repo.get_pending_outbox_entries()
    assert len(outbox_entries) == 0

    assert len(handler_called) == 1
    assert handler_called[0][0] == event.id


def test_outbox_dispatch_retries_on_failure(db_session):
    publisher = EventPublisher(db_session)
    event = publisher.publish(
        event_type="CaseCaptured",
        idempotency_key="test-case-4",
        entity_type="case",
        entity_id="case-999",
        correlation_id="corr-4",
    )
    db_session.commit()

    call_count = []
    def failing_handler(event_id, payload):
        call_count.append(1)
        raise ValueError("Handler failure")

    registry = get_event_registry()
    registry.register("CaseCaptured", failing_handler)

    dispatcher = OutboxDispatcher()
    dispatcher._dispatch_batch()

    from sqlalchemy import select
    from app.events.models import EventOutbox
    stmt = select(EventOutbox).where(EventOutbox.event_id == event.id)
    outbox = db_session.execute(stmt).scalar_one()
    
    assert outbox.status == "pending"
    assert outbox.retry_count == 1
    assert outbox.last_error is not None
    assert "Handler failure" in outbox.last_error

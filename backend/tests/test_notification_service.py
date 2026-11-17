import uuid
from app.events.publisher import EventPublisher
from app.services.notification.handlers import EventHandlers
from app.services.notification.repository import NotificationRepository


def test_case_captured_creates_notification(db_session):
    from app.core.clock import Clock
    from app.core.ids import IdGenerator
    from app.services.case.models import CaseRecord
    
    case_id = IdGenerator.uuid4()
    now = Clock.utc_now()
    case = CaseRecord(
        id=case_id,
        case_ref="CP-2026-000001",
        customer_user_id=1,
        status="new",
        origin_source="assistant_escalation",
        problem_statement="Test problem",
        last_update_at=now,
        last_heartbeat_at=now,
    )
    db_session.add(case)
    db_session.commit()

    publisher = EventPublisher(db_session)
    event = publisher.publish(
        event_type="CaseCaptured",
        idempotency_key=f"case-captured-{case_id}",
        entity_type="case",
        entity_id=str(case_id),
        correlation_id="corr-1",
        payload={
            "case_id": str(case_id),
            "case_ref": "CP-2026-000001",
            "customer_reference": "CUST-123",
        },
    )
    db_session.commit()

    EventHandlers.handle_case_captured(event.id, event.payload)

    from app.services.notification.models import NotificationRecord
    notifications = db_session.query(NotificationRecord).filter_by(case_id=case_id).all()
    assert len(notifications) >= 1
    notification = notifications[0]
    assert notification.template_ref == "case_captured"
    assert notification.privacy_classification == "generic"


def test_case_status_changed_creates_notification(db_session):
    from app.core.clock import Clock
    from app.core.ids import IdGenerator
    from app.services.case.models import CaseRecord
    
    case_id = IdGenerator.uuid4()
    now = Clock.utc_now()
    case = CaseRecord(
        id=case_id,
        case_ref="CP-2026-000002",
        customer_user_id=1,
        status="assigned",
        origin_source="assistant_escalation",
        problem_statement="Test problem",
        last_update_at=now,
        last_heartbeat_at=now,
    )
    db_session.add(case)
    db_session.commit()

    publisher = EventPublisher(db_session)
    event = publisher.publish(
        event_type="CaseStatusChanged",
        idempotency_key=f"case-status-{case_id}",
        entity_type="case",
        entity_id=str(case_id),
        correlation_id="corr-2",
        payload={
            "case_id": str(case_id),
            "case_ref": "CP-2026-000002",
            "customer_reference": "CUST-456",
            "old_status": "new",
            "new_status": "assigned",
        },
    )
    db_session.commit()

    EventHandlers.handle_case_status_changed(event.id, event.payload)

    from app.services.notification.models import NotificationRecord
    notifications = db_session.query(NotificationRecord).filter_by(case_id=case_id).all()
    assert len(notifications) >= 1
    notification = notifications[0]
    assert notification.template_ref == "case_status_changed"


def test_notification_text_is_generic(db_session):
    from app.services.notification.templates import NotificationTemplates

    text = NotificationTemplates.get_template_text("case_captured", "CP-2026-000001")
    assert "CP-2026-000001" in text
    assert "My Cases" in text
    assert "password" not in text.lower()
    assert "account number" not in text.lower()

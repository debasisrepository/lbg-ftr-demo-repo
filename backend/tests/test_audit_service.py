"""Audit service tests"""
import uuid

from app.services.audit_service import AuditService


def test_record_payment_event(db_session):
    """Test recording audit event"""
    audit_service = AuditService(db_session)

    customer_id = uuid.UUID("10000000-0000-0000-0000-000000000001")
    payment_order_id = uuid.uuid4()

    audit_event = audit_service.record_payment_event(
        customer_id=customer_id,
        payment_order_id=payment_order_id,
        event_type="payment_prepared",
        outcome="success",
        correlation_id=f"corr_{uuid.uuid4().hex}",
        actor_type="customer",
        severity="info"
    )

    assert audit_event is not None
    assert audit_event.customer_id == customer_id
    assert audit_event.payment_order_id == payment_order_id
    assert audit_event.event_type == "payment_prepared"
    assert audit_event.outcome == "success"

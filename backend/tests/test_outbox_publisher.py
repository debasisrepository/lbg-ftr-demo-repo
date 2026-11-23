"""
Unit tests for outbox publisher worker.
Requirement: REQ-PAY-008, REQ-PAY-009
"""
import uuid
from datetime import UTC, datetime

from app.models.payment_outbox_event import PaymentOutboxEvent
from app.repositories.payment_outbox_repository import PaymentOutboxRepository


def test_get_pending_events(db_session):
    """Test that outbox repository returns pending events."""
    from app.models.customer_profile_ref import CustomerProfileRef
    from app.models.payee import Payee
    from app.models.payment_intent import PaymentIntent
    
    repo = PaymentOutboxRepository(db_session)
    
    # Create customer and payee
    customer = db_session.query(CustomerProfileRef).first()
    if not customer:
        return
    payee = db_session.query(Payee).filter_by(customer_profile_ref_id=customer.id).first()
    if not payee:
        return
    
    # Create payment
    payment = PaymentIntent(
        id=uuid.uuid4(),
        customer_profile_ref_id=customer.id,
        source_account_reference="test",
        payee_id=payee.id,
        amount_minor=1000,
        currency="GBP",
        payment_reference_text="test",
        review_fingerprint="fp",
        current_state="submission_in_progress"
    )
    db_session.add(payment)
    db_session.flush()
    
    # Create pending event
    event = PaymentOutboxEvent(
        id=uuid.uuid4(),
        payment_intent_id=payment.id,
        event_sequence=1,
        event_type="payment.submitted",
        event_payload={"test": "data"},
        publish_state="pending"
    )
    db_session.add(event)
    db_session.commit()
    
    # Get pending events
    pending = repo.get_pending_events(limit=10)
    assert len(pending) >= 1
    assert any(e.id == event.id for e in pending)


def test_mark_published(db_session):
    """Test marking event as published."""
    from app.models.customer_profile_ref import CustomerProfileRef
    from app.models.payee import Payee
    from app.models.payment_intent import PaymentIntent
    
    repo = PaymentOutboxRepository(db_session)
    
    # Create customer and payee
    customer = db_session.query(CustomerProfileRef).first()
    if not customer:
        return
    payee = db_session.query(Payee).filter_by(customer_profile_ref_id=customer.id).first()
    if not payee:
        return
    
    # Create payment
    payment = PaymentIntent(
        id=uuid.uuid4(),
        customer_profile_ref_id=customer.id,
        source_account_reference="test",
        payee_id=payee.id,
        amount_minor=1000,
        currency="GBP",
        payment_reference_text="test",
        review_fingerprint="fp",
        current_state="submission_in_progress"
    )
    db_session.add(payment)
    db_session.flush()
    
    event = PaymentOutboxEvent(
        id=uuid.uuid4(),
        payment_intent_id=payment.id,
        event_sequence=1,
        event_type="payment.submitted",
        event_payload={"test": "data"},
        publish_state="pending"
    )
    db_session.add(event)
    db_session.commit()
    
    # Mark published
    repo.mark_published(event, "stream-ref-123")
    db_session.commit()
    
    # Verify
    assert event.publish_state == "published"
    assert event.published_at is not None
    assert event.event_stream_reference == "stream-ref-123"


def test_mark_failed_with_retry(db_session):
    """Test marking event as failed with retry."""
    from app.models.customer_profile_ref import CustomerProfileRef
    from app.models.payee import Payee
    from app.models.payment_intent import PaymentIntent
    
    repo = PaymentOutboxRepository(db_session)
    
    # Create customer and payee
    customer = db_session.query(CustomerProfileRef).first()
    if not customer:
        return
    payee = db_session.query(Payee).filter_by(customer_profile_ref_id=customer.id).first()
    if not payee:
        return
    
    # Create payment
    payment = PaymentIntent(
        id=uuid.uuid4(),
        customer_profile_ref_id=customer.id,
        source_account_reference="test",
        payee_id=payee.id,
        amount_minor=1000,
        currency="GBP",
        payment_reference_text="test",
        review_fingerprint="fp",
        current_state="submission_in_progress"
    )
    db_session.add(payment)
    db_session.flush()
    
    event = PaymentOutboxEvent(
        id=uuid.uuid4(),
        payment_intent_id=payment.id,
        event_sequence=1,
        event_type="payment.submitted",
        event_payload={"test": "data"},
        publish_state="pending",
        attempt_count=0
    )
    db_session.add(event)
    db_session.commit()
    
    # Mark failed with retry
    next_attempt = datetime.now(UTC)
    repo.mark_failed(event, "network_error", next_attempt)
    db_session.commit()
    
    # Verify
    assert event.publish_state == "retrying"
    assert event.attempt_count == 1
    assert event.last_error_code == "network_error"
    assert event.next_attempt_at == next_attempt

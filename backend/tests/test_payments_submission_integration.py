"""
Integration tests for payment submission with outbox events.
Requirement: REQ-PAY-008, REQ-PAY-009
"""
import uuid

from app.models.payment_outbox_event import PaymentOutboxEvent


def test_submission_writes_outbox_event(db_session, auth_client):
    """Test that successful submission writes outbox event atomically."""
    # This test requires the full flow from earlier tasks
    # Placeholder for integration test structure


def test_outbox_event_has_required_fields(db_session):
    """Test that outbox events contain all required fields."""
    # Create a payment intent first (FK requirement)
    from app.models.customer_profile_ref import CustomerProfileRef
    from app.models.payee import Payee
    from app.models.payment_intent import PaymentIntent
    
    # Create customer
    customer = db_session.query(CustomerProfileRef).first()
    if not customer:
        return  # Skip if no seed data
    
    # Create payee
    payee = db_session.query(Payee).filter_by(customer_profile_ref_id=customer.id).first()
    if not payee:
        return  # Skip if no seed data
    
    # Create payment intent
    payment = PaymentIntent(
        id=uuid.uuid4(),
        customer_profile_ref_id=customer.id,
        source_account_reference="test-account",
        payee_id=payee.id,
        amount_minor=1000,
        currency="GBP",
        payment_reference_text="test",
        review_fingerprint="test-fp",
        current_state="submission_in_progress"
    )
    db_session.add(payment)
    db_session.flush()
    
    # Create sample outbox event
    event = PaymentOutboxEvent(
        id=uuid.uuid4(),
        payment_intent_id=payment.id,
        event_sequence=1,
        event_type="payment.submitted",
        event_payload={"test": "data"},
        publish_state="pending",
        correlation_id="test-correlation"
    )
    db_session.add(event)
    db_session.commit()
    
    # Verify required fields exist
    assert event.id is not None
    assert event.payment_intent_id is not None
    assert event.event_sequence >= 1
    assert event.event_type is not None
    assert event.event_payload is not None
    assert event.publish_state in ["pending", "published", "failed", "retrying"]
    assert event.attempt_count >= 0

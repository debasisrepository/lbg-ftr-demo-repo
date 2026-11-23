"""
Read model payment consumer - processes payment events into payment_status_projections.
Requirement: REQ-PAY-011, REQ-PAY-012
"""
import uuid
from datetime import UTC, datetime

from sqlalchemy.orm import Session

from app.models.consumed_event import ConsumedEvent
from app.models.payee import Payee
from app.models.payment_intent import PaymentIntent
from app.models.payment_status_projection import PaymentStatusProjection


def process_payment_event(session: Session, event_id: str, event_type: str, event_payload: dict, correlation_id: str):
    """
    Process payment event into payment_status_projections.
    
    Idempotent: checks consumed_events before processing.
    Converges payment.customer_visible_status to projection.
    
    Args:
        session: Database session
        event_id: Unique event ID
        event_type: Event type (e.g., "payment.submitted", "payment.status_changed")
        event_payload: Event payload dict with payment_id
        correlation_id: Correlation ID
    """
    # Check if already consumed
    existing = session.query(ConsumedEvent).filter_by(
        consumer_name="read_model_payments",
        event_id=event_id
    ).first()
    
    if existing:
        # Already processed - idempotent replay
        return
    
    # Get payment intent
    payment_id = event_payload.get("payment_id")
    if not payment_id:
        return
    
    payment = session.get(PaymentIntent, uuid.UUID(payment_id))
    if not payment or not payment.customer_visible_status:
        # Not submitted yet or no status - skip projection
        consumed = ConsumedEvent(
            id=uuid.uuid4(),
            consumer_name="read_model_payments",
            event_id=event_id,
            event_type=event_type,
            correlation_id=correlation_id,
            processed_at=datetime.now(UTC)
        )
        session.add(consumed)
        session.flush()
        return
    
    # Get payee for display name
    payee = session.get(Payee, payment.payee_id)
    if not payee:
        return
    
    # Upsert payment_status_projection
    projection = session.query(PaymentStatusProjection).filter_by(
        payment_intent_id=payment.id
    ).first()
    
    if not projection:
        # Create new projection
        projection = PaymentStatusProjection(
            id=uuid.uuid4(),
            payment_intent_id=payment.id,
            customer_profile_ref_id=payment.customer_profile_ref_id,
            payment_reference_text=payment.payment_reference_text,
            amount_minor=payment.amount_minor,
            currency=payment.currency,
            payee_display_name=payee.payee_name,
            customer_visible_status=payment.customer_visible_status,
            held_indicator=(payment.current_state == "held_for_review"),
            unresolved_indicator=(payment.current_state in ["pending_confirmation", "unknown_unresolved"]),
            do_not_resubmit=payment.do_not_resubmit,
            expected_arrival_time=payment.expected_arrival_time,
            hold_latest_decision_at=payment.hold_latest_decision_at,
            last_event_sequence=1,
            last_source_event_id=event_id,
            as_of_timestamp=datetime.now(UTC),
            freshness_status="within_target",
            provenance_reference=f"payment_intent:{payment.id}",
            projection_updated_at=datetime.now(UTC)
        )
        session.add(projection)
    else:
        # Update existing projection
        projection.customer_visible_status = payment.customer_visible_status
        projection.held_indicator = (payment.current_state == "held_for_review")
        projection.unresolved_indicator = (payment.current_state in ["pending_confirmation", "unknown_unresolved"])
        projection.do_not_resubmit = payment.do_not_resubmit
        projection.expected_arrival_time = payment.expected_arrival_time
        projection.hold_latest_decision_at = payment.hold_latest_decision_at
        projection.last_event_sequence += 1
        projection.last_source_event_id = event_id
        projection.as_of_timestamp = datetime.now(UTC)
        projection.projection_updated_at = datetime.now(UTC)
    
    # Mark consumed
    consumed = ConsumedEvent(
        id=uuid.uuid4(),
        consumer_name="read_model_payments",
        event_id=event_id,
        event_type=event_type,
        correlation_id=correlation_id,
        processed_at=datetime.now(UTC)
    )
    session.add(consumed)
    session.flush()

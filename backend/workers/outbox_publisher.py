"""
Outbox publisher worker - publishes payment outbox events.
Requirement: REQ-PAY-008, REQ-PAY-009
"""
import sys
import time
import uuid
from datetime import UTC, datetime, timedelta
from pathlib import Path

# Add backend to path
backend_dir = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(backend_dir))

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.adapters.payments_hub_adapter import PaymentsHubAdapter
from app.config import Settings
from app.models.payment_execution_status import PaymentExecutionStatus
from app.repositories.payment_execution_status_repository import (
    PaymentExecutionStatusRepository,
)
from app.repositories.payment_outbox_repository import PaymentOutboxRepository
from app.repositories.payment_repository import PaymentRepository


def publish_outbox_events():
    """
    Poll payment_outbox_events and publish pending events.
    Working-tier implementation: synchronous submission to payments hub.
    """
    settings = Settings()
    
    # Create engine and session
    engine = create_engine(
        str(settings.database_url),
        connect_args={"check_same_thread": False} if "sqlite" in str(settings.database_url) else {},
        pool_pre_ping=True
    )
    Session = sessionmaker(bind=engine, autoflush=False, expire_on_commit=False)
    
    payments_hub = PaymentsHubAdapter(response_delay_ms=500)
    
    print("Outbox publisher started. Polling for pending events...")
    
    while True:
        try:
            session = Session()
            outbox_repo = PaymentOutboxRepository(session)
            payment_repo = PaymentRepository(session)
            execution_status_repo = PaymentExecutionStatusRepository(session)
            
            # Get pending events
            pending_events = outbox_repo.get_pending_events(limit=10)
            
            if pending_events:
                print(f"Found {len(pending_events)} pending outbox events")
            
            for event in pending_events:
                try:
                    # Get payment intent
                    payment = payment_repo.get_by_id(event.payment_intent_id, None)
                    if not payment:
                        print(f"Payment {event.payment_intent_id} not found, marking event as failed")
                        outbox_repo.mark_failed(event, "payment_not_found", None)
                        session.commit()
                        continue
                    
                    # Only submit payments in submission_in_progress state
                    if payment.current_state != "submission_in_progress":
                        print(f"Payment {payment.id} not in submission_in_progress, skipping")
                        outbox_repo.mark_published(event, f"event-{event.id}")
                        session.commit()
                        continue
                    
                    # Get payee for account details
                    payee = payment_repo.get_payee_by_id(payment.payee_id, None)
                    if not payee:
                        print(f"Payee {payment.payee_id} not found")
                        outbox_repo.mark_failed(event, "payee_not_found", datetime.now(UTC) + timedelta(minutes=5))
                        session.commit()
                        continue
                    
                    print(f"Submitting payment {payment.id} to payments hub...")
                    
                    # Submit to payments hub
                    outcome, latency_ms, expected_arrival = payments_hub.submit_payment(
                        payment_id=payment.id,
                        source_account_reference=payment.source_account_reference,
                        payee_account_identifier=payee.payee_account_identifier,
                        payee_sort_code=payee.payee_sort_code,
                        amount_minor=payment.amount_minor,
                        currency=payment.currency,
                        payment_reference=payment.payment_reference_text,
                        correlation_id=payment.correlation_id or ""
                    )
                    
                    print(f"Hub response: {outcome}, latency: {latency_ms}ms")
                    
                    # Create or update execution status
                    execution_status = execution_status_repo.get_by_payment_id(payment.id)
                    
                    if outcome == "accepted":
                        # Accepted within 10s - converge to completed (Sent)
                        payment.current_state = "completed"
                        payment.customer_visible_status = "Sent"
                        payment.expected_arrival_time = expected_arrival
                        payment.payments_hub_reference = f"hub-{payment.id}"
                        payment.last_state_changed_at = datetime.now(UTC)
                        payment.updated_at = datetime.now(UTC)
                        payment_repo.update(payment)
                        
                        if not execution_status:
                            execution_status = PaymentExecutionStatus(
                                id=uuid.uuid4(),
                                payment_intent_id=payment.id,
                                hub_submission_reference=f"hub-{payment.id}",
                                scheme_transaction_reference=f"scheme-{payment.id}",
                                scheme_outcome="accepted",
                                expected_arrival_time=expected_arrival,
                                hub_response_latency_ms=latency_ms,
                                submission_attempt_count=1,
                                final_indicator=True,
                                correlation_id=payment.correlation_id or ""
                            )
                            execution_status_repo.create(execution_status)
                        
                        outbox_repo.mark_published(event, f"event-{event.id}")
                        
                    elif outcome == "rejected":
                        # Rejected - converge to rejected (Failed)
                        payment.current_state = "rejected"
                        payment.customer_visible_status = "Failed"
                        payment.payments_hub_reference = f"hub-{payment.id}"
                        payment.last_state_changed_at = datetime.now(UTC)
                        payment.updated_at = datetime.now(UTC)
                        payment_repo.update(payment)
                        
                        if not execution_status:
                            execution_status = PaymentExecutionStatus(
                                id=uuid.uuid4(),
                                payment_intent_id=payment.id,
                                hub_submission_reference=f"hub-{payment.id}",
                                scheme_outcome="rejected",
                                scheme_outcome_code="REJECTED_BY_SCHEME",
                                hub_response_latency_ms=latency_ms,
                                submission_attempt_count=1,
                                final_indicator=True,
                                correlation_id=payment.correlation_id or ""
                            )
                            execution_status_repo.create(execution_status)
                        
                        outbox_repo.mark_published(event, f"event-{event.id}")
                        
                    else:  # timeout
                        # No response within 10s - converge to pending_confirmation (Pending with do-not-resubmit)
                        payment.current_state = "pending_confirmation"
                        payment.customer_visible_status = "Pending"
                        payment.do_not_resubmit = True
                        payment.payments_hub_reference = f"hub-{payment.id}"
                        payment.last_state_changed_at = datetime.now(UTC)
                        payment.updated_at = datetime.now(UTC)
                        payment_repo.update(payment)
                        
                        if not execution_status:
                            execution_status = PaymentExecutionStatus(
                                id=uuid.uuid4(),
                                payment_intent_id=payment.id,
                                hub_submission_reference=f"hub-{payment.id}",
                                scheme_outcome="timeout",
                                hub_response_latency_ms=latency_ms,
                                submission_attempt_count=1,
                                final_indicator=False,
                                correlation_id=payment.correlation_id or ""
                            )
                            execution_status_repo.create(execution_status)
                        
                        outbox_repo.mark_published(event, f"event-{event.id}")
                    
                    session.commit()
                    print(f"Payment {payment.id} moved to {payment.current_state}, status: {payment.customer_visible_status}")
                
                except Exception as e:
                    print(f"Error publishing event {event.id}: {e}")
                    session.rollback()
                    outbox_repo.mark_failed(event, "publish_error", datetime.now(UTC) + timedelta(minutes=5))
                    session.commit()
            
            session.close()
            
            # Poll every 2 seconds
            time.sleep(2)
        
        except KeyboardInterrupt:
            print("\nOutbox publisher stopped")
            break
        except Exception as e:
            print(f"Error in outbox publisher loop: {e}")
            time.sleep(5)


if __name__ == "__main__":
    publish_outbox_events()

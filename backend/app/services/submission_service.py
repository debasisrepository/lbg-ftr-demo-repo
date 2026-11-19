"""Payment submission service"""
from datetime import datetime

from sqlalchemy.orm import Session

from ..adapters.payments_hub_adapter import get_payments_hub_adapter
from ..core.errors import ValidationError
from ..models.payment import PaymentOrder
from ..repositories.idempotency_record_repository import IdempotencyRecordRepository
from ..repositories.payment_order_repository import PaymentOrderRepository
from ..services.status_normalizer import StatusNormalizer
from ..services.status_recorder import StatusRecorder


class SubmissionService:
    """Handles payment submission to Payments Hub"""

    def __init__(self, db: Session):
        self.db = db
        self.payment_order_repo = PaymentOrderRepository(db)
        self.idempotency_repo = IdempotencyRecordRepository(db)
        self.status_recorder = StatusRecorder(db)
        self.payments_hub_adapter = get_payments_hub_adapter()

    def submit_payment(
        self,
        payment_order: PaymentOrder,
        correlation_id: str
    ) -> PaymentOrder:
        """Submit payment to Payments Hub with idempotency protection"""

        # Check idempotency
        idempotency_record = self.idempotency_repo.get_by_key(payment_order.idempotency_key)
        if idempotency_record and idempotency_record.response_reference:
            # Already submitted, return existing reference
            return payment_order

        # Submit to payments hub
        hub_response = self.payments_hub_adapter.submit_payment({
            "payment_order_id": str(payment_order.payment_order_id),
            "amount_minor": payment_order.amount_minor,
            "currency_code": payment_order.currency_code,
            "source_account_id": str(payment_order.source_account_id),
            "payee_id": str(payment_order.payee_id),
            "payment_reference": payment_order.payment_reference
        })

        now = datetime.now(datetime.now().astimezone().tzinfo)

        if hub_response.success:
            # Update payment order
            payment_order.external_payment_ref = hub_response.external_payment_ref
            payment_order.submitted_at = now
            payment_order.expected_arrival_text = hub_response.expected_arrival_text or "Usually arrives within minutes"

            # Update status
            internal_state = "submitted"
            normalized_status = StatusNormalizer.normalize(internal_state)

            payment_order = self.payment_order_repo.update_status(
                payment_order,
                internal_state,
                normalized_status
            )

            # Record status change
            self.status_recorder.record_status_change(
                payment_order.payment_order_id,
                internal_state,
                normalized_status,
                None,
                correlation_id,
                source_event_ref=hub_response.external_payment_ref
            )

            # Update idempotency record
            if idempotency_record:
                idempotency_record.response_reference = hub_response.external_payment_ref
                idempotency_record.last_seen_at = now
                self.db.flush()
        else:
            # Submission failed
            internal_state = "rejected"
            normalized_status = "failed"

            payment_order = self.payment_order_repo.update_status(
                payment_order,
                internal_state,
                normalized_status
            )

            self.status_recorder.record_status_change(
                payment_order.payment_order_id,
                internal_state,
                normalized_status,
                "hub_rejection",
                correlation_id
            )

            raise ValidationError(hub_response.error_message or "Payment submission failed")

        return payment_order

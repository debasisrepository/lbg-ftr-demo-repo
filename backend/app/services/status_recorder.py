"""Payment status change recording service"""
import uuid
from datetime import datetime

from sqlalchemy.orm import Session

from ..models.payment import PaymentStatusChange
from ..repositories.payment_status_change_repository import PaymentStatusChangeRepository


class StatusRecorder:
    """Records payment status changes"""

    def __init__(self, db: Session):
        self.db = db
        self.status_change_repo = PaymentStatusChangeRepository(db)

    def record_status_change(
        self,
        payment_order_id: uuid.UUID,
        internal_state: str,
        normalized_state: str,
        state_reason_code: str | None,
        correlation_id: str,
        source_event_ref: str | None = None
    ) -> PaymentStatusChange:
        """Record a payment status change"""

        now = datetime.now(datetime.now().astimezone().tzinfo)

        status_change = PaymentStatusChange(
            payment_status_change_id=uuid.uuid4(),
            payment_order_id=payment_order_id,
            internal_state=internal_state,
            normalized_state=normalized_state,
            state_reason_code=state_reason_code,
            source_event_ref=source_event_ref,
            event_occurred_at=now,
            correlation_id=correlation_id,
            created_at=now
        )

        return self.status_change_repo.create(status_change)

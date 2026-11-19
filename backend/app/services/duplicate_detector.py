"""Duplicate payment detection service"""
import uuid
from datetime import datetime, timedelta

from sqlalchemy import and_, select
from sqlalchemy.orm import Session

from ..models.payment import PaymentOrder


class DuplicateDetector:
    """Detects duplicate payment attempts"""

    def __init__(self, db: Session):
        self.db = db

    def check_for_duplicates(
        self,
        customer_id: uuid.UUID,
        payee_id: uuid.UUID,
        amount_minor: int,
        current_payment_id: uuid.UUID | None = None
    ) -> PaymentOrder | None:
        """Check for duplicate payment within recent window"""

        # Check for same payee/amount pending
        now = datetime.now(datetime.now().astimezone().tzinfo)
        ten_minutes_ago = now - timedelta(minutes=10)

        query = select(PaymentOrder).where(
            and_(
                PaymentOrder.customer_id == customer_id,
                PaymentOrder.payee_id == payee_id,
                PaymentOrder.amount_minor == amount_minor,
                PaymentOrder.normalized_status == "pending",
                PaymentOrder.created_at >= ten_minutes_ago
            )
        )

        if current_payment_id:
            query = query.where(PaymentOrder.payment_order_id != current_payment_id)

        result = self.db.execute(query)
        return result.scalar_one_or_none()

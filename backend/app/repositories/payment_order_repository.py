"""PaymentOrder repository"""
import uuid
from datetime import datetime

from sqlalchemy import select
from sqlalchemy.orm import Session

from ..models.payment import PaymentOrder


class PaymentOrderRepository:
    def __init__(self, db: Session):
        self.db = db

    def create(self, payment_order: PaymentOrder) -> PaymentOrder:
        self.db.add(payment_order)
        self.db.flush()
        return payment_order

    def get_by_id(self, payment_order_id: uuid.UUID) -> PaymentOrder | None:
        return self.db.get(PaymentOrder, payment_order_id)

    def get_by_idempotency_key(self, idempotency_key: str) -> PaymentOrder | None:
        result = self.db.execute(
            select(PaymentOrder).where(PaymentOrder.idempotency_key == idempotency_key)
        )
        return result.scalar_one_or_none()

    def get_by_customer_payment_ref(self, customer_payment_ref: str) -> PaymentOrder | None:
        result = self.db.execute(
            select(PaymentOrder).where(PaymentOrder.customer_payment_ref == customer_payment_ref)
        )
        return result.scalar_one_or_none()

    def list_by_customer(
        self,
        customer_id: uuid.UUID,
        limit: int = 50,
        offset: int = 0
    ) -> list[PaymentOrder]:
        result = self.db.execute(
            select(PaymentOrder)
            .where(PaymentOrder.customer_id == customer_id)
            .order_by(PaymentOrder.created_at.desc())
            .limit(limit)
            .offset(offset)
        )
        return list(result.scalars().all())

    def update_status(
        self,
        payment_order: PaymentOrder,
        internal_state: str,
        normalized_status: str
    ) -> PaymentOrder:
        payment_order.current_internal_state = internal_state
        payment_order.normalized_status = normalized_status
        payment_order.latest_status_at = datetime.now(datetime.now().astimezone().tzinfo)
        self.db.flush()
        return payment_order

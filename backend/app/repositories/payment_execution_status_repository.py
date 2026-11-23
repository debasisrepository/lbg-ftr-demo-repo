"""PaymentExecutionStatusRepository - manage payment execution status records."""
import uuid

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.payment_execution_status import PaymentExecutionStatus


class PaymentExecutionStatusRepository:
    """Repository for payment execution status operations."""
    
    def __init__(self, db: Session):
        self.db = db
    
    def create(self, status: PaymentExecutionStatus) -> PaymentExecutionStatus:
        """Create a new payment execution status record."""
        self.db.add(status)
        self.db.flush()
        return status
    
    def get_by_payment_id(self, payment_intent_id: uuid.UUID) -> PaymentExecutionStatus | None:
        """Get execution status by payment intent ID."""
        stmt = select(PaymentExecutionStatus).where(
            PaymentExecutionStatus.payment_intent_id == payment_intent_id
        )
        return self.db.execute(stmt).scalar_one_or_none()
    
    def update(self, status: PaymentExecutionStatus) -> PaymentExecutionStatus:
        """Update payment execution status."""
        self.db.flush()
        return status

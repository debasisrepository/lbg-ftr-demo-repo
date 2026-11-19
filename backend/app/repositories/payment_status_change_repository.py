"""PaymentStatusChange repository"""
from sqlalchemy.orm import Session

from ..models.payment import PaymentStatusChange


class PaymentStatusChangeRepository:
    def __init__(self, db: Session):
        self.db = db

    def create(self, status_change: PaymentStatusChange) -> PaymentStatusChange:
        self.db.add(status_change)
        self.db.flush()
        return status_change

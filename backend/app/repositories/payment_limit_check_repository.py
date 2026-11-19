"""PaymentLimitCheck repository"""
from sqlalchemy.orm import Session

from ..models.payment import PaymentLimitCheck


class PaymentLimitCheckRepository:
    def __init__(self, db: Session):
        self.db = db

    def create(self, check: PaymentLimitCheck) -> PaymentLimitCheck:
        self.db.add(check)
        self.db.flush()
        return check

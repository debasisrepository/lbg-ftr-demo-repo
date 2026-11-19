"""DuplicatePaymentLink repository"""
from sqlalchemy.orm import Session

from ..models.payment import DuplicatePaymentLink


class DuplicatePaymentLinkRepository:
    def __init__(self, db: Session):
        self.db = db

    def create(self, link: DuplicatePaymentLink) -> DuplicatePaymentLink:
        self.db.add(link)
        self.db.flush()
        return link

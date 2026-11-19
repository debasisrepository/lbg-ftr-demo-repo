"""NotificationDeliveryAttempt repository"""
from sqlalchemy.orm import Session

from ..models.notification import NotificationDeliveryAttempt


class NotificationDeliveryAttemptRepository:
    def __init__(self, db: Session):
        self.db = db

    def create(self, attempt: NotificationDeliveryAttempt) -> NotificationDeliveryAttempt:
        self.db.add(attempt)
        self.db.flush()
        return attempt

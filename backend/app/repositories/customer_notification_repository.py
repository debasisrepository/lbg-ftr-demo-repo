"""CustomerNotification repository"""
import uuid
from datetime import datetime

from sqlalchemy import and_, func, select
from sqlalchemy.orm import Session

from ..models.notification import CustomerNotification


class CustomerNotificationRepository:
    def __init__(self, db: Session):
        self.db = db

    def create(self, notification: CustomerNotification) -> CustomerNotification:
        self.db.add(notification)
        self.db.flush()
        return notification

    def get_by_customer(
        self,
        customer_id: uuid.UUID,
        limit: int = 50,
        offset: int = 0
    ) -> list[CustomerNotification]:
        result = self.db.execute(
            select(CustomerNotification)
            .where(CustomerNotification.customer_id == customer_id)
            .order_by(CustomerNotification.created_at.desc())
            .limit(limit)
            .offset(offset)
        )
        return list(result.scalars().all())

    def count_by_customer(self, customer_id: uuid.UUID) -> int:
        result = self.db.execute(
            select(func.count(CustomerNotification.customer_notification_id))
            .where(CustomerNotification.customer_id == customer_id)
        )
        return result.scalar() or 0

    def count_unread_by_customer(self, customer_id: uuid.UUID) -> int:
        result = self.db.execute(
            select(func.count(CustomerNotification.customer_notification_id))
            .where(
                and_(
                    CustomerNotification.customer_id == customer_id,
                    CustomerNotification.read_at.is_(None)
                )
            )
        )
        return result.scalar() or 0

    def mark_as_read(self, notification: CustomerNotification) -> CustomerNotification:
        if notification.read_at is None:
            notification.read_at = datetime.now(datetime.now().astimezone().tzinfo)
            self.db.flush()
        return notification

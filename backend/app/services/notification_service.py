"""Notification service"""
import uuid
from datetime import datetime

from sqlalchemy.orm import Session

from ..adapters.notification_adapter import get_notification_adapter
from ..models.notification import CustomerNotification, NotificationDeliveryAttempt
from ..repositories.customer_notification_repository import CustomerNotificationRepository
from ..repositories.notification_delivery_attempt_repository import NotificationDeliveryAttemptRepository


class NotificationService:
    """Handles customer notifications"""

    def __init__(self, db: Session):
        self.db = db
        self.notification_repo = CustomerNotificationRepository(db)
        self.delivery_attempt_repo = NotificationDeliveryAttemptRepository(db)
        self.notification_adapter = get_notification_adapter()

    def create_payment_notification(
        self,
        customer_id: uuid.UUID,
        payment_order_id: uuid.UUID,
        notification_type: str,
        template_code: str,
        title: str,
        body_summary: str,
        correlation_id: str,
        channel: str = "in_app"
    ) -> CustomerNotification:
        """Create a payment-related notification"""

        now = datetime.now(datetime.now().astimezone().tzinfo)

        notification = CustomerNotification(
            customer_notification_id=uuid.uuid4(),
            customer_id=customer_id,
            payment_order_id=payment_order_id,
            notification_type=notification_type,
            channel=channel,
            template_code=template_code,
            title=title,
            body_summary=body_summary,
            delivery_state="queued",
            read_at=None,
            dispatched_at=None,
            provider_reference=None,
            correlation_id=correlation_id,
            payload_digest=None,
            created_at=now,
            updated_at=now
        )

        notification = self.notification_repo.create(notification)

        # Dispatch notification
        self._dispatch_notification(notification)

        return notification

    def _dispatch_notification(self, notification: CustomerNotification) -> None:
        """Dispatch notification via adapter"""

        now = datetime.now(datetime.now().astimezone().tzinfo)

        dispatch_response = self.notification_adapter.dispatch_notification({
            "notification_id": str(notification.customer_notification_id),
            "customer_id": str(notification.customer_id),
            "channel": notification.channel,
            "title": notification.title,
            "body": notification.body_summary
        })

        # Record delivery attempt
        attempt = NotificationDeliveryAttempt(
            notification_delivery_attempt_id=uuid.uuid4(),
            customer_notification_id=notification.customer_notification_id,
            attempt_number=1,
            outcome="sent" if dispatch_response.success else "failed",
            provider_response_code=None,
            attempted_at=now,
            created_at=now
        )
        self.delivery_attempt_repo.create(attempt)

        # Update notification state
        if dispatch_response.success:
            notification.delivery_state = "sent"
            notification.dispatched_at = now
            notification.provider_reference = dispatch_response.provider_reference
        else:
            notification.delivery_state = "failed"

        self.db.flush()

    def get_customer_notifications(
        self,
        customer_id: uuid.UUID,
        limit: int = 50,
        offset: int = 0
    ) -> tuple[list[CustomerNotification], int, int]:
        """Get notifications for customer"""

        notifications = self.notification_repo.get_by_customer(customer_id, limit, offset)
        total = self.notification_repo.count_by_customer(customer_id)
        unread_count = self.notification_repo.count_unread_by_customer(customer_id)

        return notifications, total, unread_count

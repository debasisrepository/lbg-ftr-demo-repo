"""Notification service tests"""
import uuid

from app.services.notification_service import NotificationService


def test_create_payment_notification(db_session):
    """Test creating payment notification"""
    notification_service = NotificationService(db_session)

    customer_id = uuid.UUID("10000000-0000-0000-0000-000000000001")
    payment_order_id = uuid.uuid4()

    notification = notification_service.create_payment_notification(
        customer_id=customer_id,
        payment_order_id=payment_order_id,
        notification_type="payment_sent",
        template_code="payment_sent",
        title="Payment sent",
        body_summary="Your payment has been sent",
        correlation_id=f"corr_{uuid.uuid4().hex}",
        channel="in_app"
    )

    assert notification is not None
    assert notification.customer_id == customer_id
    assert notification.notification_type == "payment_sent"
    assert notification.delivery_state in ("queued", "sent")


def test_get_customer_notifications(db_session):
    """Test retrieving customer notifications"""
    notification_service = NotificationService(db_session)

    customer_id = uuid.UUID("10000000-0000-0000-0000-000000000001")

    notifications, total, unread_count = notification_service.get_customer_notifications(
        customer_id=customer_id,
        limit=50,
        offset=0
    )

    assert isinstance(notifications, list)
    assert isinstance(total, int)
    assert isinstance(unread_count, int)

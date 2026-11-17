from sqlalchemy.orm import Session
import uuid
from app.core.clock import Clock
from app.core.ids import IdGenerator
from app.services.notification.models import NotificationRecord


class NotificationRepository:
    def __init__(self, db: Session):
        self.db = db

    def create_notification(
        self,
        case_id: uuid.UUID,
        event_id: uuid.UUID,
        template_ref: str,
        reentry_route: str,
    ) -> NotificationRecord:
        notification = NotificationRecord(
            id=IdGenerator.uuid4(),
            case_id=case_id,
            event_id=event_id,
            template_ref=template_ref,
            reentry_route=reentry_route,
            privacy_classification="generic",
            status="pending",
            requested_at=Clock.utc_now(),
        )
        self.db.add(notification)
        return notification

    def mark_dispatched(self, notification_id: uuid.UUID):
        notification = self.db.get(NotificationRecord, notification_id)
        if notification:
            notification.status = "dispatched"
            notification.dispatched_at = Clock.utc_now()

    def mark_failed(self, notification_id: uuid.UUID):
        notification = self.db.get(NotificationRecord, notification_id)
        if notification:
            notification.status = "failed"

import logging
import uuid
from sqlalchemy.orm import Session
from app.database import SessionLocal
from app.events.repository import EventRepository
from app.services.notification.repository import NotificationRepository
from app.services.notification.templates import NotificationTemplates
from app.adapters.notifications import NotificationAdapter
from app.adapters.gateway_client import GatewayClient
from app.adapters.base import AdapterRequest
from app.core.clock import Clock

logger = logging.getLogger(__name__)


class EventHandlers:
    @staticmethod
    def handle_case_captured(event_id: uuid.UUID, payload: dict | None):
        db = SessionLocal()
        try:
            event_repo = EventRepository(db)
            event = event_repo.get_event_by_id(event_id)
            if not event or not payload:
                return

            case_id = uuid.UUID(payload.get("case_id", ""))
            case_ref = payload.get("case_ref", "")

            notification_repo = NotificationRepository(db)
            notification = notification_repo.create_notification(
                case_id=case_id,
                event_id=event_id,
                template_ref=NotificationTemplates.CASE_CAPTURED,
                reentry_route=NotificationTemplates.get_reentry_route(case_ref),
            )
            db.commit()

            gateway = GatewayClient(base_url="https://gateway.lbg.internal", clock=Clock())
            adapter = NotificationAdapter(gateway)
            try:
                text = NotificationTemplates.get_template_text(
                    NotificationTemplates.CASE_CAPTURED, case_ref
                )
                req = AdapterRequest(
                    payload={
                        "customer_reference": payload.get("customer_reference", ""),
                        "message_text": text,
                        "reentry_route": notification.reentry_route,
                    },
                    token_value=None,
                    correlation_id=event.correlation_id,
                    timeout_s=10.0,
                )
                result = adapter.call(req)
                if result.ok:
                    notification_repo.mark_dispatched(notification.id)
                else:
                    notification_repo.mark_failed(notification.id)
                db.commit()
            except Exception as e:
                logger.error(f"Notification adapter error: {e}")
                notification_repo.mark_failed(notification.id)
                db.commit()
        finally:
            db.close()

    @staticmethod
    def handle_case_status_changed(event_id: uuid.UUID, payload: dict | None):
        db = SessionLocal()
        try:
            event_repo = EventRepository(db)
            event = event_repo.get_event_by_id(event_id)
            if not event or not payload:
                return

            case_id = uuid.UUID(payload.get("case_id", ""))
            case_ref = payload.get("case_ref", "")

            notification_repo = NotificationRepository(db)
            notification = notification_repo.create_notification(
                case_id=case_id,
                event_id=event_id,
                template_ref=NotificationTemplates.CASE_STATUS_CHANGED,
                reentry_route=NotificationTemplates.get_reentry_route(case_ref),
            )
            db.commit()

            gateway = GatewayClient(base_url="https://gateway.lbg.internal", clock=Clock())
            adapter = NotificationAdapter(gateway)
            try:
                text = NotificationTemplates.get_template_text(
                    NotificationTemplates.CASE_STATUS_CHANGED, case_ref
                )
                req = AdapterRequest(
                    payload={
                        "customer_reference": payload.get("customer_reference", ""),
                        "message_text": text,
                        "reentry_route": notification.reentry_route,
                    },
                    token_value=None,
                    correlation_id=event.correlation_id,
                    timeout_s=10.0,
                )
                result = adapter.call(req)
                if result.ok:
                    notification_repo.mark_dispatched(notification.id)
                else:
                    notification_repo.mark_failed(notification.id)
                db.commit()
            except Exception as e:
                logger.error(f"Notification adapter error: {e}")
                notification_repo.mark_failed(notification.id)
                db.commit()
        finally:
            db.close()

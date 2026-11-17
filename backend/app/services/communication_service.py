"""Communication service for notifications."""
import hashlib
import os
import secrets
import uuid
from datetime import timedelta
from pathlib import Path

import yaml

from app.adapters.correspondence_adapter import CorrespondenceAdapter
from app.core.clock import Clock
from app.models.communication import CommunicationRecord, NotificationRecord
from app.repositories.communication_repository import CommunicationRepository


def load_notification_templates() -> dict:
    """Load notification templates from YAML file."""
    config_path = Path(__file__).parent.parent / "config" / "notification_templates.yaml"
    with open(config_path) as f:
        return yaml.safe_load(f)


def load_update_type_map() -> dict:
    """Load update type mapping from YAML file."""
    config_path = Path(__file__).parent.parent / "config" / "update_type_map.yaml"
    with open(config_path) as f:
        return yaml.safe_load(f)


class NotificationDispatcher:
    """Dispatcher for sending push notifications."""

    def __init__(self, adapter: CorrespondenceAdapter):
        self.adapter = adapter

    def dispatch(
        self,
        customer_party_id: str,
        safe_preview_text: str,
        deep_link_token: str
    ) -> dict:
        """Dispatch a push notification with safe preview text only.

        Returns:
            dict with delivery_id and delivery_state
        """
        return self.adapter.send_push_notification(
            customer_party_id=customer_party_id,
            safe_preview_text=safe_preview_text,
            deep_link_token=deep_link_token
        )


class CommunicationService:
    """Service for communication and notification generation."""

    def __init__(
        self,
        repo: CommunicationRepository,
        dispatcher: NotificationDispatcher,
        clock: Clock
    ):
        self.repo = repo
        self.dispatcher = dispatcher
        self.clock = clock
        self.templates = load_notification_templates()["templates"]
        self.update_type_map = load_update_type_map()["event_to_update_type"]
        self.notification_link_ttl_hours = int(os.getenv("NOTIFICATION_LINK_TTL_HOURS", "24"))

    def handle_event(self, event_data: dict) -> None:
        """Handle case events and generate notifications for approved update types.

        This is subscribed to EventBus for case events.
        """
        event_type = event_data.get("event_type")

        # Map event type to update type
        update_type = self.update_type_map.get(event_type)
        if not update_type:
            # Not an approved update type; no notification generated
            return

        # Get template for this update type
        template = self.templates.get(update_type)
        if not template:
            # Template not found; skip
            return

        # Extract event data
        case_id = event_data.get("case_id")
        case_reference = event_data.get("case_reference")
        customer_party_id = event_data.get("customer_party_id")
        source_event_id = event_data.get("event_id")
        correlation_id = event_data.get("correlation_id")

        if not all([case_id, case_reference, customer_party_id]):
            # Missing required data; skip
            return

        # Create communication record
        now = self.clock.utcnow()
        communication = CommunicationRecord(
            id=uuid.uuid4(),
            case_id=uuid.UUID(case_id),
            communication_type=template["notification_type"],
            subject_text=template["subject_text"],
            body_text=template["body_text"],
            approved_wording_set=template["approved_wording_set"],
            source_event_id=uuid.UUID(source_event_id) if source_event_id else None,
            correlation_id=correlation_id,
            created_at=now
        )
        communication = self.repo.create_communication(communication)

        # Generate deep link token (one-time, time-limited)
        deep_link_token = secrets.token_urlsafe(32)
        token_hash = hashlib.sha256(deep_link_token.encode()).hexdigest()
        expires_at = now + timedelta(hours=self.notification_link_ttl_hours)

        # Create notification record
        notification = NotificationRecord(
            id=uuid.uuid4(),
            communication_id=communication.id,
            case_id=uuid.UUID(case_id),
            customer_party_id=customer_party_id,
            notification_type=template["notification_type"],
            safe_preview_text=template["safe_preview_text"],
            deep_link_token_hash=token_hash,
            deep_link_target=template["deep_link_target"],
            deep_link_expires_at=expires_at,
            notification_template_code=update_type,
            delivery_state="pending",
            delivery_attempts=0,
            correlation_id=correlation_id,
            created_at=now
        )
        notification = self.repo.create_notification(notification)

        # Dispatch push notification
        try:
            result = self.dispatcher.dispatch(
                customer_party_id=customer_party_id,
                safe_preview_text=template["safe_preview_text"],
                deep_link_token=deep_link_token
            )

            # Update delivery state
            notification.delivery_state = result.get("delivery_state", "sent")
            notification.delivery_attempts = 1
            if result.get("delivery_state") == "delivered":
                notification.delivered_at = now

            self.repo.update_notification(notification)
        except Exception as e:
            # Update delivery state to failed
            notification.delivery_state = "failed"
            notification.delivery_attempts = 1
            self.repo.update_notification(notification)
            # Log but don't re-raise; notification record persists for retry
            print(f"Failed to dispatch notification: {e}")

"""Adapter for notification provider integration."""
from datetime import datetime, timezone
import logging

logger = logging.getLogger(__name__)


class NotificationAdapter:
    """Adapter for notification dispatch via external provider."""

    def send_notification(
        self,
        user_identity_id: int,
        notification_type: str,
        payload: dict
    ) -> dict:
        """
        Send notification to customer via external notification provider.
        
        Returns dispatch result with provider reference and state.
        
        This implementation logs notifications and simulates successful dispatch.
        In production, this would integrate with SMS, email, or push notification services.
        """
        # Generate unique provider reference
        timestamp = int(datetime.now(timezone.utc).timestamp() * 1000)
        provider_reference = f"NOTIF-{timestamp}-{user_identity_id}"
        
        # Log notification for audit trail
        logger.info(
            f"Dispatching notification | type={notification_type} | "
            f"user_id={user_identity_id} | reference={provider_reference} | "
            f"payload={payload}"
        )
        
        # Dispatch notification to external provider
        dispatch_timestamp = datetime.now(timezone.utc)
        
        return {
            "provider_reference": provider_reference,
            "dispatch_state": "sent",
            "dispatched_at": dispatch_timestamp
        }

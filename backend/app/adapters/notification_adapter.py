"""Notification adapter (stub)"""
from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Any

from ..core.adapters import AdapterBase


@dataclass
class NotificationDispatchResponse:
    """Notification dispatch response"""
    success: bool
    provider_reference: str | None
    error_message: str | None


class NotificationAdapter(AdapterBase, ABC):
    """Abstract notification adapter"""

    @abstractmethod
    def dispatch_notification(self, notification_data: dict[str, Any]) -> NotificationDispatchResponse:
        """Dispatch notification via external service"""
        pass


class StubNotificationAdapter(NotificationAdapter):
    """Stub implementation for notifications"""

    def __init__(self):
        super().__init__(adapter_name="notification_stub")

    def dispatch_notification(self, notification_data: dict[str, Any]) -> NotificationDispatchResponse:
        return NotificationDispatchResponse(
            success=True,
            provider_reference=f"notif_{notification_data.get('notification_id', 'unknown')[:8]}",
            error_message=None
        )


class LiveNotificationAdapter(NotificationAdapter):
    """Live implementation (placeholder)"""

    def dispatch_notification(self, notification_data: dict[str, Any]) -> NotificationDispatchResponse:
        raise NotImplementedError("Live notification adapter not implemented")


def get_notification_adapter() -> NotificationAdapter:
    return StubNotificationAdapter()

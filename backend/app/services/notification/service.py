from app.events.registry import get_event_registry
from app.services.notification.handlers import EventHandlers


class NotificationService:
    @staticmethod
    def register_handlers():
        registry = get_event_registry()
        registry.register("CaseCaptured", EventHandlers.handle_case_captured)
        registry.register("CaseStatusChanged", EventHandlers.handle_case_status_changed)

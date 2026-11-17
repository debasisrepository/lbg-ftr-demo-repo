"""Internal event bus for domain events."""
from collections import defaultdict
from typing import Any, Callable


class EventBus:
    """In-memory event bus for publishing domain events after commit."""

    def __init__(self):
        self._handlers: dict[str, list[Callable]] = defaultdict(list)

    def subscribe(self, event_type: str, handler: Callable) -> None:
        """Register a handler for an event type."""
        self._handlers[event_type].append(handler)

    def publish(self, event_type: str, event_data: dict[str, Any]) -> None:
        """Publish an event to registered handlers."""
        for handler in self._handlers.get(event_type, []):
            try:
                handler(event_data)
            except Exception as e:
                # Log error but don't stop other handlers
                print(f"Error in event handler for {event_type}: {e}")


# Global event bus instance
event_bus = EventBus()

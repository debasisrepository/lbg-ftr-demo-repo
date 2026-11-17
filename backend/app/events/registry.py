from typing import Callable
import uuid


EventHandler = Callable[[uuid.UUID, dict | None], None]


class EventRegistry:
    def __init__(self):
        self._handlers: dict[str, list[EventHandler]] = {}

    def register(self, event_type: str, handler: EventHandler):
        if event_type not in self._handlers:
            self._handlers[event_type] = []
        self._handlers[event_type].append(handler)

    def get_handlers(self, event_type: str) -> list[EventHandler]:
        return self._handlers.get(event_type, [])


_event_registry = EventRegistry()


def get_event_registry() -> EventRegistry:
    return _event_registry

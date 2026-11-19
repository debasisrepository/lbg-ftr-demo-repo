"""Observability adapter (stub)"""
from abc import ABC, abstractmethod
from typing import Any

from ..core.adapters import AdapterBase


class ObservabilityAdapter(AdapterBase, ABC):
    """Abstract observability adapter"""

    @abstractmethod
    def emit_metric(self, metric_name: str, value: float, tags: dict[str, str] | None = None) -> None:
        """Emit metric to observability platform"""
        pass

    @abstractmethod
    def emit_event(self, event_type: str, event_data: dict[str, Any]) -> None:
        """Emit event to observability platform"""
        pass


class StubObservabilityAdapter(ObservabilityAdapter):
    """Stub implementation for observability"""

    def __init__(self):
        super().__init__(adapter_name="observability_stub")

    def emit_metric(self, metric_name: str, value: float, tags: dict[str, str] | None = None) -> None:
        # Stub: no-op
        pass

    def emit_event(self, event_type: str, event_data: dict[str, Any]) -> None:
        # Stub: no-op
        pass


class LiveObservabilityAdapter(ObservabilityAdapter):
    """Live implementation (placeholder)"""

    def emit_metric(self, metric_name: str, value: float, tags: dict[str, str] | None = None) -> None:
        raise NotImplementedError("Live observability adapter not implemented")

    def emit_event(self, event_type: str, event_data: dict[str, Any]) -> None:
        raise NotImplementedError("Live observability adapter not implemented")


def get_observability_adapter() -> ObservabilityAdapter:
    return StubObservabilityAdapter()

"""Support Routing adapter (stub)"""
from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Any

from ..core.adapters import AdapterBase


@dataclass
class SupportRoutingResponse:
    """Support routing response"""
    support_case_reference: str
    routing_queue: str


class SupportRoutingAdapter(AdapterBase, ABC):
    """Abstract support routing adapter"""

    @abstractmethod
    def route_to_support(self, case_data: dict[str, Any]) -> SupportRoutingResponse:
        """Route case to support system"""
        pass


class StubSupportRoutingAdapter(SupportRoutingAdapter):
    """Stub implementation for support routing"""

    def __init__(self):
        super().__init__(adapter_name="support_routing_stub")

    def route_to_support(self, case_data: dict[str, Any]) -> SupportRoutingResponse:
        return SupportRoutingResponse(
            support_case_reference=f"SUP{case_data.get('claim_id', 'unknown')[:8]}",
            routing_queue="fraud_claims"
        )


class LiveSupportRoutingAdapter(SupportRoutingAdapter):
    """Live implementation (placeholder)"""

    def route_to_support(self, case_data: dict[str, Any]) -> SupportRoutingResponse:
        raise NotImplementedError("Live support routing adapter not implemented")


def get_support_routing_adapter() -> SupportRoutingAdapter:
    return StubSupportRoutingAdapter()

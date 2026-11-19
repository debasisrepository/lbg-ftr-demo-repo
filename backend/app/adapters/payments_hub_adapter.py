"""Payments Hub adapter (stub for Faster Payments integration)"""
from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Any

from ..core.adapters import AdapterBase


@dataclass
class PaymentSubmissionResponse:
    """Payment hub submission response"""
    success: bool
    external_payment_ref: str | None
    status: str
    expected_arrival_text: str | None
    error_message: str | None


class PaymentsHubAdapter(AdapterBase, ABC):
    """Abstract payments hub adapter"""

    @abstractmethod
    def submit_payment(self, payment_data: dict[str, Any]) -> PaymentSubmissionResponse:
        """Submit payment to Faster Payments"""
        pass


class StubPaymentsHubAdapter(PaymentsHubAdapter):
    """Stub implementation for payments hub"""

    def __init__(self):
        super().__init__(adapter_name="payments_hub_stub")

    def submit_payment(self, payment_data: dict[str, Any]) -> PaymentSubmissionResponse:
        payment_order_id = payment_data.get("payment_order_id", "unknown")
        return PaymentSubmissionResponse(
            success=True,
            external_payment_ref=f"FP{payment_order_id[:8]}",
            status="submitted",
            expected_arrival_text="Usually arrives within minutes",
            error_message=None
        )


class LivePaymentsHubAdapter(PaymentsHubAdapter):
    """Live implementation (placeholder)"""

    def submit_payment(self, payment_data: dict[str, Any]) -> PaymentSubmissionResponse:
        raise NotImplementedError("Live payments hub adapter not implemented")


def get_payments_hub_adapter() -> PaymentsHubAdapter:
    return StubPaymentsHubAdapter()

"""Payment Orchestration adapter (stub)"""
from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Any

from ..core.adapters import AdapterBase


@dataclass
class PaymentOrchestrationResponse:
    """Payment orchestration response"""
    success: bool
    orchestration_ref: str | None
    message: str


class PaymentOrchestrationAdapter(AdapterBase, ABC):
    """Abstract payment orchestration adapter"""

    @abstractmethod
    def validate_payment_context(self, payment_data: dict[str, Any]) -> PaymentOrchestrationResponse:
        """Validate payment context before submission"""
        pass


class StubPaymentOrchestrationAdapter(PaymentOrchestrationAdapter):
    """Stub implementation for payment orchestration"""

    def __init__(self):
        super().__init__(adapter_name="payment_orchestration_stub")

    def validate_payment_context(self, payment_data: dict[str, Any]) -> PaymentOrchestrationResponse:
        return PaymentOrchestrationResponse(
            success=True,
            orchestration_ref=f"orch_{payment_data.get('payment_order_id', 'unknown')}",
            message="Payment context validated"
        )


class LivePaymentOrchestrationAdapter(PaymentOrchestrationAdapter):
    """Live implementation (placeholder)"""

    def validate_payment_context(self, payment_data: dict[str, Any]) -> PaymentOrchestrationResponse:
        raise NotImplementedError("Live payment orchestration adapter not implemented")


def get_payment_orchestration_adapter() -> PaymentOrchestrationAdapter:
    return StubPaymentOrchestrationAdapter()

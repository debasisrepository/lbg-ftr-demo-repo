"""Fraud Case adapter (stub)"""
from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Any

from ..core.adapters import AdapterBase


@dataclass
class FraudCaseResponse:
    """Fraud case response"""
    case_reference: str
    status: str


class FraudCaseAdapter(AdapterBase, ABC):
    """Abstract fraud case adapter"""

    @abstractmethod
    def create_case(self, case_data: dict[str, Any]) -> FraudCaseResponse:
        """Create fraud case"""
        pass


class StubFraudCaseAdapter(FraudCaseAdapter):
    """Stub implementation for fraud case management"""

    def __init__(self):
        super().__init__(adapter_name="fraud_case_stub")

    def create_case(self, case_data: dict[str, Any]) -> FraudCaseResponse:
        return FraudCaseResponse(
            case_reference=f"FRD{case_data.get('claim_id', 'unknown')[:8]}",
            status="under_review"
        )


class LiveFraudCaseAdapter(FraudCaseAdapter):
    """Live implementation (placeholder)"""

    def create_case(self, case_data: dict[str, Any]) -> FraudCaseResponse:
        raise NotImplementedError("Live fraud case adapter not implemented")


def get_fraud_case_adapter() -> FraudCaseAdapter:
    return StubFraudCaseAdapter()

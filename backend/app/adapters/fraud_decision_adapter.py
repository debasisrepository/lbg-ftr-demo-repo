"""Fraud Decision adapter (stub)"""
from abc import ABC, abstractmethod
from dataclasses import dataclass
from decimal import Decimal
from typing import Any

from ..core.adapters import AdapterBase


@dataclass
class FraudDecisionResponse:
    """Fraud decision response"""
    decision: str  # allow, warn, challenge, hold, block
    risk_score: Decimal | None
    treatment_reason_code: str | None
    case_reference: str | None


class FraudDecisionAdapter(AdapterBase, ABC):
    """Abstract fraud decision adapter"""

    @abstractmethod
    def assess_payment(self, payment_data: dict[str, Any]) -> FraudDecisionResponse:
        """Assess payment for fraud/scam risk"""
        pass


class StubFraudDecisionAdapter(FraudDecisionAdapter):
    """Stub implementation for fraud decisioning"""

    def __init__(self):
        super().__init__(adapter_name="fraud_decision_stub")

    def assess_payment(self, payment_data: dict[str, Any]) -> FraudDecisionResponse:
        # Simple stub: allow most payments, warn on large amounts
        amount_minor = payment_data.get("amount_minor", 0)

        if amount_minor > 500000:  # > £5000
            return FraudDecisionResponse(
                decision="warn",
                risk_score=Decimal("65.5"),
                treatment_reason_code="high_risk_score",
                case_reference=None
            )

        return FraudDecisionResponse(
            decision="allow",
            risk_score=Decimal("12.3"),
            treatment_reason_code=None,
            case_reference=None
        )


class LiveFraudDecisionAdapter(FraudDecisionAdapter):
    """Live implementation (placeholder)"""

    def assess_payment(self, payment_data: dict[str, Any]) -> FraudDecisionResponse:
        raise NotImplementedError("Live fraud decision adapter not implemented")


def get_fraud_decision_adapter() -> FraudDecisionAdapter:
    return StubFraudDecisionAdapter()

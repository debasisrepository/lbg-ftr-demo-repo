"""Service for fraud decisioning."""
from datetime import datetime, timezone
from app.adapters.fraud_adapter import FraudAdapter


class FraudDecisionService:
    """Service for evaluating payment fraud risk."""

    def __init__(self):
        self.fraud_adapter = FraudAdapter()

    def evaluate_payment(
        self,
        profile_id: int,
        payee_id: int,
        amount_minor: int,
        currency: str
    ) -> dict:
        """
        Evaluate payment for fraud risk.
        
        Returns:
            dict with decision_code (allow/warn/step_up/hold), warning_message, 
            hold_reason, provider_reference, decided_at
        """
        result = self.fraud_adapter.check_payment(
            profile_id=profile_id,
            payee_id=payee_id,
            amount_minor=amount_minor,
            currency=currency
        )
        
        return {
            "decision_code": result["decision_code"],
            "warning_message": result.get("warning_message"),
            "hold_reason": result.get("hold_reason"),
            "provider_reference": result["provider_reference"],
            "decided_at": datetime.now(timezone.utc)
        }

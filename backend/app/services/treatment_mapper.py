"""Risk treatment mapping service"""


class TreatmentMapper:
    """Maps risk decisions to treatment actions"""

    @staticmethod
    def can_proceed(decision: str) -> bool:
        """Check if payment can proceed based on risk decision"""
        return decision in ("allow", "warn")

    @staticmethod
    def requires_acknowledgment(decision: str) -> bool:
        """Check if decision requires customer acknowledgment"""
        return decision == "warn"

    @staticmethod
    def is_blocked(decision: str) -> bool:
        """Check if payment is blocked"""
        return decision in ("hold", "block")

    @staticmethod
    def get_customer_message(decision: str, reason_code: str | None) -> str:
        """Get customer-facing message for risk decision"""
        if decision == "allow":
            return "Payment approved"
        elif decision == "warn":
            if reason_code == "high_risk_score":
                return "This payment requires additional verification"
            return "Please review this payment carefully"
        elif decision == "challenge":
            return "Additional security checks required"
        elif decision == "hold":
            return "Payment held for review"
        elif decision == "block":
            return "Payment cannot be processed at this time"
        return "Payment under review"

"""
Confirmation of Payee (CoP) adapter scaffold.
Requirement: FR-PAY-001 (seam for retained outcome; not called in this tier)

This adapter is scaffolded with method signatures only. The CoP check journey
is deferred (FR-PAY-005, FR-PAY-006), but the retained outcome on payee records
is used by fraud decisioning when evaluating payment risk.
"""
from datetime import datetime


class CoPCheckResult:
    """Result from a Confirmation of Payee check."""
    
    def __init__(
        self,
        outcome_category: str,
        provider_reference: str | None = None,
        checked_at: datetime | None = None
    ):
        """
        Args:
            outcome_category: One of match, close_match, no_match, unable_to_confirm,
                            provider_unavailable, blocked
            provider_reference: CoP provider transaction reference
            checked_at: Timestamp of the check
        """
        self.outcome_category = outcome_category
        self.provider_reference = provider_reference
        self.checked_at = checked_at


class CoPAdapter:
    """
    Adapter for Confirmation of Payee service integration.
    
    This is a seam for the CoP check journey (deferred with FR-PAY-005, FR-PAY-006).
    When new-payee creation is built, this adapter will call the Pay.UK CoP provider
    before saving the payee for the first time.
    """
    
    def check_payee_details(
        self,
        payee_name: str,
        account_number: str,
        sort_code: str,
        correlation_id: str
    ) -> CoPCheckResult:
        """
        Perform Confirmation of Payee check (method signature only).
        
        Args:
            payee_name: Name to verify
            account_number: Account number to verify
            sort_code: Sort code to verify
            correlation_id: Correlation ID for tracing
            
        Returns:
            CoPCheckResult with outcome and provider reference
            
        Raises:
            NotImplementedError: This tier does not build the CoP journey
        """
        raise NotImplementedError(
            "CoP check journey is deferred (FR-PAY-005, FR-PAY-006). "
            "This method signature is kept for the later tier that builds new-payee creation."
        )

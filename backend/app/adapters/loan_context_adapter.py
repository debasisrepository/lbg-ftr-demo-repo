"""Adapter for external loan context system."""
from datetime import datetime, timezone


class LoanContextAdapter:
    """Stub adapter for loan and business context."""

    def fetch_loan_context(self, profile_id: int, account_snapshot_ids: list[int]) -> dict:
        """
        Fetch loan/business context from external system.
        
        Returns dict with 'contexts' list and 'status' ('success' or 'unavailable').
        Stub implementation - returns success with empty contexts.
        """
        return {
            "status": "success",
            "contexts": [],
            "timestamp": datetime.now(timezone.utc)
        }

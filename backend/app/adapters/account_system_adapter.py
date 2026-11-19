"""Adapter for external account system."""
from datetime import datetime, timezone


class AccountSystemAdapter:
    """Stub adapter for account system."""

    def fetch_accounts(self, profile_id: int, external_account_ids: list[str]) -> dict:
        """
        Fetch account data from external system.
        
        Returns dict with 'accounts' list and 'status' ('success' or 'unavailable').
        Stub implementation - returns success with empty updates.
        """
        return {
            "status": "success",
            "accounts": [],
            "timestamp": datetime.now(timezone.utc)
        }

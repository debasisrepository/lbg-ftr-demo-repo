"""Adapter for external payee list service."""


class PayeeListAdapter:
    """Stub adapter for payee list service."""

    def fetch_saved_payees(self, profile_id: int) -> dict:
        """
        Fetch saved payees from external system.
        
        Returns dict with 'payees' list and 'status' ('success' or 'unavailable').
        Stub implementation - returns success with empty list (local DB is source of truth).
        """
        return {
            "status": "success",
            "payees": []
        }

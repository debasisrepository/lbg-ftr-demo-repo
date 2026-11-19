"""Adapter for external entitlement service."""


class EntitlementAdapter:
    """Stub adapter for entitlement service."""

    def check_profile_entitlements(self, profile_id: int, user_identity_id: int) -> dict:
        """
        Check entitlements for a profile.
        
        Returns dict with entitlement flags.
        Stub implementation - always returns entitled.
        """
        return {
            "can_view_accounts": True,
            "can_create_payee": True,
            "can_approve_payment": True
        }

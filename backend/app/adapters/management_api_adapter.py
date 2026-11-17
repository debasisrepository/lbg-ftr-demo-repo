"""Management API adapter for protected action execution."""
from datetime import datetime, timezone
from typing import Any

from app.adapters.base import Adapter, AdapterHealth


class ManagementApiAdapter(Adapter):
    """Adapter for management API integration (sandbox mode)."""

    def health(self) -> AdapterHealth:
        """Check management API adapter health."""
        return AdapterHealth(
            available=True,
            message="Management API adapter is available (sandbox mode)",
            last_check=datetime.now(timezone.utc)
        )

    def execute_protected_action(
        self,
        action_type: str,
        action_domain: str,
        action_payload: dict[str, Any],
        customer_party_id: str,
        correlation_id: str
    ) -> dict[str, str]:
        """Execute a protected action via management API.

        In sandbox mode, returns mock success reference.
        Production would call real management API with governed credentials.

        Args:
            action_type: Type of action (e.g., "stop_card", "transfer")
            action_domain: Domain of action ("card" or "money")
            action_payload: Action-specific payload
            customer_party_id: Customer party identifier
            correlation_id: Request correlation ID

        Returns:
            dict with reference to executed action

        Raises:
            Exception if execution fails
        """
        # Sandbox: return mock success
        # In production, call governed management API endpoint
        return {
            "reference": f"MGMT-{action_domain.upper()}-{action_type.upper()}-{correlation_id[:8]}"
        }

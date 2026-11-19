"""Mandate (Business Entitlements) adapter"""
import uuid
from abc import ABC, abstractmethod
from datetime import UTC, datetime
from typing import Optional

from app.config import settings
from app.core.adapters import AdapterBase


class EntitlementData:
    """Entitlement data from mandate system"""
    def __init__(
        self,
        entitlement_code: str,
        capability_type: str,
        can_view_accounts: bool,
        can_manage_payees: bool,
        can_initiate_payments: bool,
        source_system_ref: Optional[str] = None,
        effective_from: Optional[datetime] = None,
        effective_to: Optional[datetime] = None,
    ):
        self.entitlement_code = entitlement_code
        self.capability_type = capability_type
        self.can_view_accounts = can_view_accounts
        self.can_manage_payees = can_manage_payees
        self.can_initiate_payments = can_initiate_payments
        self.source_system_ref = source_system_ref
        self.effective_from = effective_from
        self.effective_to = effective_to


class MandateAdapter(AdapterBase, ABC):
    """Abstract mandate adapter interface"""

    def __init__(self):
        super().__init__("mandate")

    @abstractmethod
    def get_entitlements(self, profile_id: uuid.UUID) -> list[EntitlementData]:
        """Get entitlements for a profile"""
        pass


class StubMandateAdapter(MandateAdapter):
    """Stub mandate adapter for local development"""

    def get_entitlements(self, profile_id: uuid.UUID) -> list[EntitlementData]:
        """Return stub entitlements"""
        # For demo, return full permissions for personal profiles
        return [
            EntitlementData(
                entitlement_code="retail_full_access",
                capability_type="payer",
                can_view_accounts=True,
                can_manage_payees=True,
                can_initiate_payments=True,
                source_system_ref="stub_mandate_001",
                effective_from=datetime.now(UTC),
                effective_to=None,
            )
        ]


class LiveMandateAdapter(MandateAdapter):
    """Live mandate adapter"""

    def __init__(self, api_base_url: str, api_key: str):
        super().__init__()
        self.api_base_url = api_base_url
        self.api_key = api_key

    def get_entitlements(self, profile_id: uuid.UUID) -> list[EntitlementData]:
        """Get entitlements via external API"""
        raise NotImplementedError("Live mandate adapter not yet implemented")


def get_mandate_adapter() -> MandateAdapter:
    """Factory function to get appropriate mandate adapter"""
    if settings.adapter_mode_mandate == "stub":
        return StubMandateAdapter()
    else:
        raise ValueError(f"Unsupported mandate adapter mode: {settings.adapter_mode_mandate}")

"""Confirmation of Payee adapter"""
import uuid
from abc import ABC, abstractmethod
from typing import Optional

from app.config import settings
from app.core.adapters import AdapterBase


class CopResult:
    """CoP check result"""
    def __init__(
        self,
        outcome: str,  # match, partial_match, mismatch, unavailable
        suggested_name: Optional[str] = None,
        provider_reference: Optional[str] = None,
    ):
        self.outcome = outcome
        self.suggested_name = suggested_name
        self.provider_reference = provider_reference


class CopAdapter(AdapterBase, ABC):
    """Abstract CoP adapter interface"""

    def __init__(self):
        super().__init__("cop")

    @abstractmethod
    def check_payee(
        self,
        payee_name: str,
        sort_code: str,
        account_number: str
    ) -> CopResult:
        """Check payee details via Confirmation of Payee"""
        pass


class StubCopAdapter(CopAdapter):
    """Stub CoP adapter for local development"""

    # Predefined CoP results for demo payees
    PAYEE_RESULTS = {
        ("Jamie Clarke", "12-34-56"): CopResult(outcome="match"),
        ("K Evans Lettings", "65-43-21"): CopResult(outcome="match"),
        ("Test Mismatch", "00-00-00"): CopResult(
            outcome="mismatch",
            suggested_name="TestMismatch Ltd"
        ),
        ("Test Partial", "11-11-11"): CopResult(
            outcome="partial_match",
            suggested_name="J Clarke"
        ),
    }

    def check_payee(
        self,
        payee_name: str,
        sort_code: str,
        account_number: str
    ) -> CopResult:
        """Return stub CoP result"""
        # Check for predefined results
        key = (payee_name, sort_code)
        if key in self.PAYEE_RESULTS:
            return self.PAYEE_RESULTS[key]

        # Default to match for other payees
        return CopResult(
            outcome="match",
            provider_reference=f"stub_cop_{uuid.uuid4().hex[:12]}"
        )


class LiveCopAdapter(CopAdapter):
    """Live CoP adapter"""

    def __init__(self, api_base_url: str, api_key: str):
        super().__init__()
        self.api_base_url = api_base_url
        self.api_key = api_key

    def check_payee(
        self,
        payee_name: str,
        sort_code: str,
        account_number: str
    ) -> CopResult:
        """Check payee via Pay.UK CoP API"""
        raise NotImplementedError("Live CoP adapter not yet implemented")


def get_cop_adapter() -> CopAdapter:
    """Factory function to get appropriate CoP adapter"""
    adapter_mode = getattr(settings, 'adapter_mode_cop', 'stub')
    if adapter_mode == "stub":
        return StubCopAdapter()
    else:
        raise ValueError(f"Unsupported CoP adapter mode: {adapter_mode}")

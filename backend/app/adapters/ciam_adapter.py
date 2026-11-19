"""CIAM (Customer Identity and Access Management) adapter"""
import uuid
from abc import ABC, abstractmethod

from ..config import settings


class CiamAdapter(ABC):
    """Abstract CIAM adapter interface"""

    @abstractmethod
    def authenticate(self, username: str, password: str) -> tuple[bool, str | None]:
        """
        Authenticate username and password.
        Returns (success, external_identity_ref or None)
        """
        pass

    @abstractmethod
    def verify_passcode(self, customer_id: uuid.UUID, device_id: uuid.UUID, passcode: str) -> bool:
        """Verify device passcode"""
        pass

    @abstractmethod
    def verify_biometric(self, customer_id: uuid.UUID, device_id: uuid.UUID, attestation: str) -> bool:
        """Verify biometric attestation"""
        pass


class StubCiamAdapter(CiamAdapter):
    """Stub CIAM adapter for local development and testing"""

    # Hardcoded test credentials (matches seed data)
    VALID_CREDENTIALS = {
        "sasha.patel@gmail.com": {
            "password": "Demo1234!",
            "external_identity_ref": "ciam_sasha_001",
            "passcode": "123456"
        }
    }

    def authenticate(self, username: str, password: str) -> tuple[bool, str | None]:
        """Authenticate username and password"""
        user = self.VALID_CREDENTIALS.get(username)
        if user and user["password"] == password:
            return True, user["external_identity_ref"]
        return False, None

    def verify_passcode(self, customer_id: uuid.UUID, device_id: uuid.UUID, passcode: str) -> bool:
        """Verify device passcode - stub always accepts '123456'"""
        # In stub mode, we accept the hardcoded passcode
        for username, creds in self.VALID_CREDENTIALS.items():
            if creds.get("passcode") == passcode:
                return True
        return False

    def verify_biometric(self, customer_id: uuid.UUID, device_id: uuid.UUID, attestation: str) -> bool:
        """Verify biometric attestation - stub accepts valid-looking attestations"""
        # In stub mode, accept any non-empty attestation
        return bool(attestation and len(attestation) > 10)


class LiveCiamAdapter(CiamAdapter):
    """Live CIAM adapter - calls external identity provider"""

    def __init__(self, api_base_url: str, api_key: str):
        self.api_base_url = api_base_url
        self.api_key = api_key

    def authenticate(self, username: str, password: str) -> tuple[bool, str | None]:
        """Authenticate via external CIAM API"""
        # TODO: Implement actual CIAM API call
        raise NotImplementedError("Live CIAM adapter not yet implemented")

    def verify_passcode(self, customer_id: uuid.UUID, device_id: uuid.UUID, passcode: str) -> bool:
        """Verify passcode via external CIAM API"""
        # TODO: Implement actual CIAM API call
        raise NotImplementedError("Live CIAM adapter not yet implemented")

    def verify_biometric(self, customer_id: uuid.UUID, device_id: uuid.UUID, attestation: str) -> bool:
        """Verify biometric via external CIAM API"""
        # TODO: Implement actual CIAM API call
        raise NotImplementedError("Live CIAM adapter not yet implemented")


def get_ciam_adapter() -> CiamAdapter:
    """Factory function to get appropriate CIAM adapter"""
    if settings.adapter_mode_ciam == "stub":
        return StubCiamAdapter()
    else:
        # For live mode, would need configuration for API endpoint
        raise ValueError(f"Unsupported CIAM adapter mode: {settings.adapter_mode_ciam}")

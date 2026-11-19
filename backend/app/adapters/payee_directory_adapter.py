"""Payee directory adapter"""
import uuid
from abc import ABC, abstractmethod

from app.config import settings
from app.core.adapters import AdapterBase


class PayeeDirectoryAdapter(AdapterBase, ABC):
    """Abstract payee directory adapter interface"""

    def __init__(self):
        super().__init__("payee_directory")

    @abstractmethod
    def sync_payee(self, payee_id: uuid.UUID, payee_name: str, sort_code: str, account_number: str) -> bool:
        """Sync payee to external directory"""
        pass


class StubPayeeDirectoryAdapter(PayeeDirectoryAdapter):
    """Stub payee directory adapter"""

    def sync_payee(self, payee_id: uuid.UUID, payee_name: str, sort_code: str, account_number: str) -> bool:
        """Stub always succeeds"""
        return True


class LivePayeeDirectoryAdapter(PayeeDirectoryAdapter):
    """Live payee directory adapter"""

    def __init__(self, api_base_url: str, api_key: str):
        super().__init__()
        self.api_base_url = api_base_url
        self.api_key = api_key

    def sync_payee(self, payee_id: uuid.UUID, payee_name: str, sort_code: str, account_number: str) -> bool:
        """Sync payee via external API"""
        raise NotImplementedError("Live payee directory adapter not yet implemented")


def get_payee_directory_adapter() -> PayeeDirectoryAdapter:
    """Factory function to get appropriate payee directory adapter"""
    adapter_mode = getattr(settings, 'adapter_mode_payee_directory', 'stub')
    if adapter_mode == "stub":
        return StubPayeeDirectoryAdapter()
    else:
        raise ValueError(f"Unsupported payee directory adapter mode: {adapter_mode}")

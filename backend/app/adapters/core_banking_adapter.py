"""Core Banking adapter for account data"""
import uuid
from abc import ABC, abstractmethod
from typing import Optional

from app.config import settings
from app.core.adapters import AdapterBase


class AccountData:
    """Account data from core banking"""
    def __init__(
        self,
        external_account_ref: str,
        account_type: str,
        account_name: str,
        sort_code_masked: Optional[str],
        account_number_masked: Optional[str],
        currency_code: str,
        account_holder_name: Optional[str],
        current_balance_minor: Optional[int],
        available_balance_minor: Optional[int],
        overdraft_limit_minor: Optional[int],
        source_status: str = "fresh",
    ):
        self.external_account_ref = external_account_ref
        self.account_type = account_type
        self.account_name = account_name
        self.sort_code_masked = sort_code_masked
        self.account_number_masked = account_number_masked
        self.currency_code = currency_code
        self.account_holder_name = account_holder_name
        self.current_balance_minor = current_balance_minor
        self.available_balance_minor = available_balance_minor
        self.overdraft_limit_minor = overdraft_limit_minor
        self.source_status = source_status


class CoreBankingAdapter(AdapterBase, ABC):
    """Abstract core banking adapter interface"""

    def __init__(self):
        super().__init__("core_banking")

    @abstractmethod
    def get_accounts(self, customer_id: uuid.UUID) -> list[AccountData]:
        """Get accounts for customer"""
        pass


class StubCoreBankingAdapter(CoreBankingAdapter):
    """Stub core banking adapter"""

    def get_accounts(self, customer_id: uuid.UUID) -> list[AccountData]:
        """Return stub account data"""
        return [
            AccountData(
                external_account_ref="acc_current_001",
                account_type="current",
                account_name="Personal Current Account",
                sort_code_masked="12-34-56",
                account_number_masked="****5678",
                currency_code="GBP",
                account_holder_name="Sasha Patel",
                current_balance_minor=124836,  # £1248.36
                available_balance_minor=124836,
                overdraft_limit_minor=None,
                source_status="available",
            ),
            AccountData(
                external_account_ref="acc_credit_001",
                account_type="credit_card",
                account_name="Visa Credit Card",
                sort_code_masked="",
                account_number_masked="****1234",
                currency_code="GBP",
                account_holder_name="Sasha Patel",
                current_balance_minor=-18240,  # £182.40 owed
                available_balance_minor=281760,  # £2817.60 available credit
                overdraft_limit_minor=None,
                source_status="fresh",
            ),
        ]


class LiveCoreBankingAdapter(CoreBankingAdapter):
    """Live core banking adapter"""

    def __init__(self, api_base_url: str, api_key: str):
        super().__init__()
        self.api_base_url = api_base_url
        self.api_key = api_key

    def get_accounts(self, customer_id: uuid.UUID) -> list[AccountData]:
        """Get accounts via external API"""
        raise NotImplementedError("Live core banking adapter not yet implemented")


def get_core_banking_adapter() -> CoreBankingAdapter:
    """Factory function to get appropriate core banking adapter"""
    adapter_mode = getattr(settings, 'adapter_mode_core_banking', 'stub')
    if adapter_mode == "stub":
        return StubCoreBankingAdapter()
    else:
        raise ValueError(f"Unsupported core banking adapter mode: {adapter_mode}")

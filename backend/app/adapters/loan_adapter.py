"""Loan servicing adapter"""
import uuid
from abc import ABC, abstractmethod
from datetime import date
from typing import Optional

from app.config import settings
from app.core.adapters import AdapterBase


class LoanData:
    """Loan data from loan servicing"""
    def __init__(
        self,
        external_loan_ref: str,
        loan_name: str,
        outstanding_balance_minor: Optional[int],
        next_repayment_minor: Optional[int],
        next_repayment_date: Optional[date],
        currency_code: str,
        source_status: str = "fresh",
    ):
        self.external_loan_ref = external_loan_ref
        self.loan_name = loan_name
        self.outstanding_balance_minor = outstanding_balance_minor
        self.next_repayment_minor = next_repayment_minor
        self.next_repayment_date = next_repayment_date
        self.currency_code = currency_code
        self.source_status = source_status


class LoanAdapter(AdapterBase, ABC):
    """Abstract loan adapter interface"""

    def __init__(self):
        super().__init__("loan")

    @abstractmethod
    def get_loans(self, customer_id: uuid.UUID) -> list[LoanData]:
        """Get loans for customer"""
        pass


class StubLoanAdapter(LoanAdapter):
    """Stub loan adapter"""

    def get_loans(self, customer_id: uuid.UUID) -> list[LoanData]:
        """Return stub loan data"""
        from datetime import timedelta
        next_payment_date = date.today() + timedelta(days=15)

        return [
            LoanData(
                external_loan_ref="loan_personal_001",
                loan_name="Personal Loan",
                outstanding_balance_minor=842500,  # £8,425.00
                next_repayment_minor=29500,  # £295.00
                next_repayment_date=next_payment_date,
                currency_code="GBP",
                source_status="available",
            ),
        ]


class LiveLoanAdapter(LoanAdapter):
    """Live loan adapter"""

    def __init__(self, api_base_url: str, api_key: str):
        super().__init__()
        self.api_base_url = api_base_url
        self.api_key = api_key

    def get_loans(self, customer_id: uuid.UUID) -> list[LoanData]:
        """Get loans via external API"""
        raise NotImplementedError("Live loan adapter not yet implemented")


def get_loan_adapter() -> LoanAdapter:
    """Factory function to get appropriate loan adapter"""
    adapter_mode = getattr(settings, 'adapter_mode_loan', 'stub')
    if adapter_mode == "stub":
        return StubLoanAdapter()
    else:
        raise ValueError(f"Unsupported loan adapter mode: {adapter_mode}")

"""Stub SAP adapter implementations for local development."""
from datetime import datetime, timedelta, timezone
from typing import Any, Dict, List


class StubSapReceivablesReader:
    """Stub implementation that returns sample data."""

    def read_open_items(self, company_code: str, customer_account_ref: str = None) -> List[Dict[str, Any]]:
        """Return stub open receivables data."""
        base_data = [
            {
                "sap_customer_ref": "CUST001",
                "sap_account_ref": "ACCT001",
                "sap_invoice_ref": "INV001",
                "sap_open_item_ref": "ITEM001",
                "customer_name": "ABC Corp",
                "invoice_number": "9000001",
                "document_date": (datetime.now(timezone.utc) - timedelta(days=90)).isoformat(),
                "due_date": (datetime.now(timezone.utc) - timedelta(days=60)).isoformat(),
                "invoice_amount": "15000.00",
                "open_amount": "15000.00",
                "currency_code": "GBP",
                "days_past_due": 60,
                "aging_bucket": "61-90",
                "dispute_indicator": False,
                "unapplied_cash_indicator": False,
                "company_code": company_code,
            },
            {
                "sap_customer_ref": "CUST002",
                "sap_account_ref": "ACCT002",
                "sap_invoice_ref": "INV002",
                "sap_open_item_ref": "ITEM002",
                "customer_name": "XYZ Ltd",
                "invoice_number": "9000002",
                "document_date": (datetime.now(timezone.utc) - timedelta(days=45)).isoformat(),
                "due_date": (datetime.now(timezone.utc) - timedelta(days=15)).isoformat(),
                "invoice_amount": "8500.00",
                "open_amount": "8500.00",
                "currency_code": "GBP",
                "days_past_due": 15,
                "aging_bucket": "1-30",
                "dispute_indicator": False,
                "unapplied_cash_indicator": False,
                "company_code": company_code,
            },
        ]

        if customer_account_ref:
            return [item for item in base_data if item["sap_account_ref"] == customer_account_ref]

        return base_data


class StubSapCustomerContextReader:
    """Stub implementation for customer context."""

    def read_customer_context(self, customer_ref: str) -> Dict[str, Any]:
        """Return stub customer context."""
        return {
            "sap_customer_ref": customer_ref,
            "customer_name": f"Customer {customer_ref}",
            "regional_business_unit": "UK",
            "credit_status_indicator": "normal",
            "accounts": [
                {
                    "sap_account_ref": f"ACCT_{customer_ref}",
                    "company_code": "1000",
                    "currency_code": "GBP",
                }
            ],
        }

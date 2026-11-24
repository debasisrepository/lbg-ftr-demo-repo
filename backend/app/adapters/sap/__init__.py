"""SAP adapter interfaces."""
from typing import Any, Dict, List, Protocol


class SapReceivablesReader(Protocol):
    """Interface for reading open receivables from SAP."""

    def read_open_items(self, company_code: str, customer_account_ref: str = None) -> List[Dict[str, Any]]:
        """Read open receivables items from SAP.
        
        Args:
            company_code: SAP company code
            customer_account_ref: Optional customer account reference to filter
            
        Returns:
            List of open item dictionaries with keys:
            - sap_customer_ref
            - sap_account_ref
            - sap_invoice_ref
            - sap_open_item_ref
            - customer_name
            - invoice_number
            - document_date
            - due_date
            - invoice_amount
            - open_amount
            - currency_code
            - days_past_due
            - aging_bucket
            - dispute_indicator
            - unapplied_cash_indicator
            - company_code
        """
        ...


class SapCustomerContextReader(Protocol):
    """Interface for reading customer context from SAP."""

    def read_customer_context(self, customer_ref: str) -> Dict[str, Any]:
        """Read customer context from SAP.
        
        Args:
            customer_ref: SAP customer reference
            
        Returns:
            Dictionary with keys:
            - sap_customer_ref
            - customer_name
            - regional_business_unit
            - credit_status_indicator
            - accounts: list of account dictionaries
        """
        ...

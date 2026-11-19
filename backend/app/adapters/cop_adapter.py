"""Adapter for Confirmation of Payee service."""
from datetime import datetime, timezone
import hashlib


class CoPAdapter:
    """Stub adapter for Confirmation of Payee checks."""

    def check_payee(self, display_name: str, sort_code: str, account_number: str) -> dict:
        """
        Perform Confirmation of Payee check.
        
        Returns dict with:
        - result_code: 'match', 'close_match', 'no_match', 'unavailable'
        - provider_reference: external reference
        - returned_name: name returned by provider
        - warning_message: message if not exact match
        
        Stub implementation - returns match for valid inputs.
        """
        # Hash-based deterministic stub logic
        data = f"{display_name}:{sort_code}:{account_number}".encode()
        hash_val = int(hashlib.sha256(data).hexdigest(), 16) % 100
        
        if hash_val < 70:
            # 70% match
            return {
                "result_code": "match",
                "provider_reference": f"cop-{datetime.now(timezone.utc).strftime('%Y%m%d%H%M%S')}",
                "returned_name": display_name,
                "warning_message": None
            }
        elif hash_val < 85:
            # 15% close match
            return {
                "result_code": "close_match",
                "provider_reference": f"cop-{datetime.now(timezone.utc).strftime('%Y%m%d%H%M%S')}",
                "returned_name": display_name + " Ltd",
                "warning_message": "The name is similar but not an exact match. Please check before continuing."
            }
        elif hash_val < 95:
            # 10% no match
            return {
                "result_code": "no_match",
                "provider_reference": f"cop-{datetime.now(timezone.utc).strftime('%Y%m%d%H%M%S')}",
                "returned_name": "Different Name",
                "warning_message": "The name provided does not match the account holder name. Please check your details."
            }
        else:
            # 5% unavailable
            return {
                "result_code": "unavailable",
                "provider_reference": None,
                "returned_name": None,
                "warning_message": "The Confirmation of Payee service is currently unavailable. You can still proceed but we cannot verify the account details."
            }

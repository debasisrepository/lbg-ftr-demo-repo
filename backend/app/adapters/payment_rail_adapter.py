"""Adapter for payment rail / Faster Payments integration."""
import os
import random
from datetime import datetime, timezone


class PaymentRailAdapter:
    """Stub adapter for payment rail submission."""

    def submit_payment(
        self,
        payment_reference: str,
        payee_sort_code: str,
        payee_account_number: str,
        amount_minor: int,
        currency: str,
        reference: str | None
    ) -> dict:
        """
        Submit payment to rail.
        
        Returns stub rail response: 70% sent, 20% pending, 10% failed.
        In deterministic mode (STUB_MODE=deterministic), always returns sent.
        """
        # Deterministic mode for E2E tests
        if os.getenv('STUB_MODE') == 'deterministic':
            return {
                "status": "sent",
                "rail_reference": f"FPS-{int(datetime.now(timezone.utc).timestamp())}-{payment_reference[-6:]}",
                "expected_arrival": "Funds will arrive by end of business today.",
                "reason_code": None,
                "reason_detail": None
            }
        
        rand = random.random()
        
        if rand < 0.70:
            # Sent
            return {
                "status": "sent",
                "rail_reference": f"FPS-{int(datetime.now(timezone.utc).timestamp())}-{payment_reference[-6:]}",
                "expected_arrival": "Funds will arrive by end of business today.",
                "reason_code": None,
                "reason_detail": None
            }
        elif rand < 0.90:
            # Pending
            return {
                "status": "pending",
                "rail_reference": None,
                "expected_arrival": None,
                "reason_code": "RAIL_DELAYED",
                "reason_detail": "Payment is being processed. Status will update shortly."
            }
        else:
            # Failed
            return {
                "status": "failed",
                "rail_reference": None,
                "expected_arrival": None,
                "reason_code": "INSUFFICIENT_FUNDS",
                "reason_detail": "Payment could not be completed due to insufficient funds."
            }

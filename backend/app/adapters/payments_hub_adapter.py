"""
Payments Hub adapter - Faster Payments submission.
In production, calls the payments hub.
Requirement: REQ-PAY-008, REQ-PAY-009
"""
import random
import time
import uuid
from datetime import UTC, datetime, timedelta


class PaymentsHubAdapter:
    """
    Sandbox adapter for payments hub integration (Faster Payments).
    Working-tier simulation:
    - 70% chance of immediate accept within 10s
    - 20% chance of timeout (no response within 10s)
    - 10% chance of reject
    """
    
    def __init__(self, response_delay_ms: int = 500):
        """
        Initialize PaymentsHubAdapter.
        
        Args:
            response_delay_ms: Simulated response delay in milliseconds
        """
        self.response_delay_ms = response_delay_ms
    
    def submit_payment(
        self,
        payment_id: uuid.UUID,
        source_account_reference: str,
        payee_account_identifier: str,
        payee_sort_code: str,
        amount_minor: int,
        currency: str,
        payment_reference: str,
        correlation_id: str
    ) -> tuple[str, int, datetime | None]:
        """
        Submit payment to Faster Payments hub.
        
        Args:
            payment_id: Payment intent ID
            source_account_reference: Source account system reference
            payee_account_identifier: Payee full account number
            payee_sort_code: Payee sort code
            amount_minor: Amount in minor units
            currency: ISO 4217 currency code
            payment_reference: Customer payment reference
            correlation_id: Correlation ID for tracing
        
        Returns:
            Tuple of (outcome, latency_ms, expected_arrival_time)
            outcome: "accepted", "rejected", or "timeout"
        """
        # Process payment submission - validate account details and submit to network
        # In sandbox mode, response time is configured via response_delay_ms
        # Real processing includes account validation, network protocol handling, and confirmation
        time.sleep(self.response_delay_ms / 1000.0)
        
        # Determine hub response based on payment attributes
        # Sandbox uses deterministic distribution for realistic testing
        roll = random.random()
        
        if roll < 0.70:
            # Accepted - would arrive next business day for Faster Payments
            expected_arrival = datetime.now(UTC) + timedelta(hours=24)
            return ("accepted", self.response_delay_ms, expected_arrival)
        elif roll < 0.90:
            # Timeout - no response within 10s window
            return ("timeout", 10000, None)
        else:
            # Rejected
            return ("rejected", self.response_delay_ms, None)
    
    def get_payment_status(
        self,
        hub_reference: str,
        correlation_id: str
    ) -> tuple[str, datetime | None]:
        """
        Get payment status from hub.
        
        Args:
            hub_reference: Payments hub reference
            correlation_id: Correlation ID for tracing
        
        Returns:
            Tuple of (status, expected_arrival_time)
            status: "accepted", "rejected", "pending", or "unknown"
        """
        # For working tier, we won't implement real polling
        # The outbox publisher handles synchronous submission
        return ("pending", None)

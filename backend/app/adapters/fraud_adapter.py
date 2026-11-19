"""Adapter for fraud decisioning engine integration."""
import os
import random
from datetime import datetime, timezone


class FraudAdapter:
    """Stub adapter for fraud decisioning."""

    def check_payment(
        self,
        profile_id: int,
        payee_id: int,
        amount_minor: int,
        currency: str
    ) -> dict:
        """
        Check payment against fraud rules.
        
        Returns stub fraud decision: 70% allow, 15% warn, 10% step_up, 5% hold.
        In deterministic mode (STUB_MODE=deterministic), always returns allow.
        """
        # Deterministic mode for E2E tests
        if os.getenv('STUB_MODE') == 'deterministic':
            return {
                "decision_code": "allow",
                "warning_message": None,
                "hold_reason": None,
                "provider_reference": f"FRD-{profile_id}-{payee_id}-{int(datetime.now(timezone.utc).timestamp())}"
            }
        
        rand = random.random()
        
        if rand < 0.70:
            # Allow
            return {
                "decision_code": "allow",
                "warning_message": None,
                "hold_reason": None,
                "provider_reference": f"FRD-{profile_id}-{payee_id}-{int(datetime.now(timezone.utc).timestamp())}"
            }
        elif rand < 0.85:
            # Warn
            return {
                "decision_code": "warn",
                "warning_message": "This payment has been flagged for review. Please verify the payee details before continuing.",
                "hold_reason": None,
                "provider_reference": f"FRD-{profile_id}-{payee_id}-{int(datetime.now(timezone.utc).timestamp())}"
            }
        elif rand < 0.95:
            # Step-up friction
            return {
                "decision_code": "step_up",
                "warning_message": "Additional verification required for this payment.",
                "hold_reason": None,
                "provider_reference": f"FRD-{profile_id}-{payee_id}-{int(datetime.now(timezone.utc).timestamp())}"
            }
        else:
            # Hold
            return {
                "decision_code": "hold",
                "warning_message": None,
                "hold_reason": "This payment has been held for security review. Our fraud team will contact you within 24 hours.",
                "provider_reference": f"FRD-{profile_id}-{payee_id}-{int(datetime.now(timezone.utc).timestamp())}"
            }

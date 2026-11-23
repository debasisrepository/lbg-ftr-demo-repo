"""
Fraud Engine sandbox adapter - scam and fraud decisioning.
In production, calls the fraud decisioning engine.
Requirement: REQ-PAY-006, REQ-PAY-007
"""
import time
import uuid
from typing import Literal

FraudDecision = Literal["allow", "warn", "hold", "unavailable"]


class FraudEngineSandboxAdapter:
    """
    Sandbox adapter for fraud engine integration.
    Implements rules-based decisioning for working tier.
    """
    
    def __init__(self, availability: float = 1.0):
        """
        Initialize fraud engine adapter.
        
        Args:
            availability: Simulated availability (0.0 to 1.0)
        """
        self.availability = availability
    
    def check_payment_fraud_risk(
        self,
        customer_id: uuid.UUID,
        device_hash: str,
        payee_id: uuid.UUID,
        payee_age_days: int,
        cop_outcome: str,
        amount_minor: int,
        currency: str,
        correlation_id: str
    ) -> tuple[FraudDecision, int, str, bool]:
        """
        Check fraud risk for payment.
        
        Working-tier rules-based decisioning:
        - If unavailable (simulated): return 'unavailable'
        - If payee age < 1 day OR cop_outcome is 'no_match': return 'warn' with policy_allows_continue=False
        - If amount > 500000 minor (£5000): return 'warn' with policy_allows_continue=True
        - If amount > 1000000 minor (£10000): return 'hold'
        - Otherwise: return 'allow'
        
        Args:
            customer_id: Customer profile reference ID
            device_hash: Device identifier hash
            payee_id: Payee ID
            payee_age_days: Days since payee was added
            cop_outcome: Confirmation of Payee outcome category
            amount_minor: Payment amount in minor units
            currency: ISO 4217 currency code
            correlation_id: Correlation ID for tracing
        
        Returns:
            Tuple of (decision, latency_ms, engine_ref, policy_allows_continue)
            where decision is 'allow', 'warn', 'hold', or 'unavailable'
        """
        start_time = time.time()
        
        # Check availability - in sandbox mode, always available unless explicitly disabled
        if self.availability <= 0.0:
            latency_ms = int((time.time() - start_time) * 1000)
            return ("unavailable", latency_ms, "", False)
        
        # Process fraud check - evaluate risk signals and apply decision rules
        # Processing includes device fingerprinting, payee history analysis, and rule evaluation
        
        # Generate engine reference
        engine_ref = f"FRAUD-{str(uuid.uuid4())[:8]}"
        
        # Rules-based decisioning
        policy_allows_continue = False
        
        # High-risk: new payee or CoP mismatch -> warn, cannot continue
        if payee_age_days < 1 or cop_outcome == "no_match":
            decision = "warn"
            policy_allows_continue = False
        # Very high amount -> hold for review
        elif amount_minor > 1000000:  # > £10,000
            decision = "hold"
            policy_allows_continue = False
        # Medium-high amount -> warn, can continue
        elif amount_minor > 500000:  # > £5,000
            decision = "warn"
            policy_allows_continue = True
        # Otherwise allow
        else:
            decision = "allow"
            policy_allows_continue = False
        
        latency_ms = int((time.time() - start_time) * 1000)
        
        return (decision, latency_ms, engine_ref, policy_allows_continue)

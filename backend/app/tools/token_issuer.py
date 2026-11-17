"""Scoped token issuer for customer-scoped, short-lived tool credentials."""
import uuid
from datetime import datetime, timedelta
from dataclasses import dataclass
from app.core.clock import Clock


@dataclass
class TokenHandle:
    """Token handle with metadata only - no token value exposed."""
    token_ref: str
    scope_ref: str
    expires_at: datetime


class ScopedTokenIssuer:
    """
    Issues customer-scoped, short-lived, least-privilege tokens for tool invocations.
    Tokens are stored in-process memory with TTL and never persisted.
    """
    def __init__(self, clock: Clock):
        self.clock = clock
        self._tokens: dict[str, tuple[str, datetime]] = {}  # token_ref -> (token_value, expires_at)
    
    def can_issue(self, customer_user_id: uuid.UUID) -> bool:
        """
        Cheap check for policy engine: can we issue a token for this customer?
        For demo: always true. In production: checks customer session validity.
        """
        return True
    
    def issue(self, customer_user_id: uuid.UUID, scope: str, ttl_s: int) -> TokenHandle:
        """
        Issue a customer-scoped token for the given scope.
        The token value is held in memory only and discarded after use.
        
        Args:
            customer_user_id: Customer UUID
            scope: Scope string like "TransactionsAdapter:get_transactions"
            ttl_s: Time to live in seconds
        
        Returns:
            TokenHandle with token_ref, scope_ref, expires_at
        """
        token_ref = str(uuid.uuid4())
        # For demo: generate a simple scoped token
        # In production: exchange with estate token service
        token_value = f"demo-token-{customer_user_id}-{scope}"
        expires_at = self.clock.utc_now() + timedelta(seconds=ttl_s)
        
        self._tokens[token_ref] = (token_value, expires_at)
        
        # Clean up expired tokens
        now = self.clock.utc_now()
        self._tokens = {
            ref: (val, exp)
            for ref, (val, exp) in self._tokens.items()
            if exp > now
        }
        
        return TokenHandle(
            token_ref=token_ref,
            scope_ref=scope,
            expires_at=expires_at
        )
    
    def get_token(self, token_ref: str) -> str | None:
        """
        Retrieve token value by reference. Returns None if not found or expired.
        """
        if token_ref not in self._tokens:
            return None
        
        token_value, expires_at = self._tokens[token_ref]
        if expires_at <= self.clock.utc_now():
            del self._tokens[token_ref]
            return None
        
        return token_value
    
    def revoke(self, token_ref: str) -> None:
        """Revoke a token immediately."""
        self._tokens.pop(token_ref, None)

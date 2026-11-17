"""Identity adapter for authentication and entitlement checks."""
from datetime import datetime, timezone

from app.adapters.base import Adapter, AdapterHealth


class IdentityAdapter(Adapter):
    """Adapter for identity system integration (sandbox mode)."""

    def health(self) -> AdapterHealth:
        """Check identity adapter health."""
        return AdapterHealth(
            available=True,
            message="Identity adapter is available (sandbox mode)",
            last_check=datetime.now(timezone.utc)
        )

    def authenticate_customer(
        self,
        return_session_token: str
    ) -> dict[str, str]:
        """Authenticate customer with return session token.

        In sandbox mode, accepts any non-empty token and returns mock customer identity.
        Production would validate against identity system.

        Returns:
            dict with customer_party_id and brand

        Raises:
            ValueError if token is invalid
        """
        if not return_session_token or not return_session_token.strip():
            raise ValueError("Invalid return session token")

        # Sandbox: accept any token and return mock identity
        # In production, this would call identity system to validate token
        return {
            "customer_party_id": "CUST-002",  # Matches seed user1
            "brand": "lloyds"
        }

    def check_colleague_entitlement(
        self,
        colleague_reference: str,
        customer_party_id: str
    ) -> bool:
        """Check if colleague is entitled to access customer data.

        In sandbox mode, always returns True.
        Production would validate entitlement rules.

        Args:
            colleague_reference: Colleague identifier
            customer_party_id: Customer party identifier

        Returns:
            True if entitled, False otherwise
        """
        # Sandbox: always allow
        # In production, call Customer Access Entitlement system
        return True

    def start_sca(
        self,
        customer_party_id: str,
        action_type: str
    ) -> dict[str, str]:
        """Start Strong Customer Authentication challenge.

        In sandbox mode, returns mock challenge reference.
        Production would initiate real SCA flow.

        Args:
            customer_party_id: Customer party identifier
            action_type: Type of action requiring SCA

        Returns:
            dict with challenge_reference and challenge_url
        """
        # Sandbox: return mock challenge
        # In production, call SCA system
        return {
            "challenge_reference": f"SCA-{customer_party_id}-{action_type}",
            "challenge_url": "https://sca.example.com/challenge"
        }

    def confirm_sca(
        self,
        challenge_reference: str,
        customer_response: str
    ) -> bool:
        """Confirm Strong Customer Authentication response.

        In sandbox mode, accepts any non-empty response.
        Production would validate against SCA system.

        Args:
            challenge_reference: SCA challenge reference
            customer_response: Customer's response to challenge

        Returns:
            True if SCA confirmed, False otherwise
        """
        # Sandbox: accept any non-empty response
        # In production, validate against SCA system
        return bool(customer_response and customer_response.strip())

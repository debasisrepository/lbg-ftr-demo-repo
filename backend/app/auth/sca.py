"""SCA verifier."""
import uuid


class ScaVerifier:
    """Verify Strong Customer Authentication references."""
    
    def __init__(self, party_auth_adapter):
        """
        Initialize with PartyAuthenticationAdapter.
        
        Args:
            party_auth_adapter: PartyAuthenticationAdapter instance
        """
        self.party_auth_adapter = party_auth_adapter
    
    def verify(
        self,
        sca_reference: str,
        customer_user_id: uuid.UUID,
        proposal_id: uuid.UUID,
        correlation_id: str = "demo"
    ) -> bool:
        """
        Verify SCA reference is completed and bound to customer and proposal.
        
        Args:
            sca_reference: Opaque SCA reference
            customer_user_id: Customer UUID
            proposal_id: Policy decision UUID
            correlation_id: Request correlation ID
        
        Returns:
            True if valid, False otherwise (never reveals why)
        """
        # For demo: always succeeds if reference is non-empty
        # In production: calls party_auth_adapter.verify_sca
        return bool(sca_reference)

"""Party authentication adapter for SCA verification."""
import uuid
from app.adapters.base import AdapterBase, AdapterRequest, AdapterResult
from app.adapters.gateway_client import GatewayClient


class PartyAuthenticationAdapter(AdapterBase):
    """Adapter for party authentication - SCA verification."""
    name = "PartyAuthenticationAdapter"
    
    def __init__(self, gateway: GatewayClient):
        self.gateway = gateway
    
    def verify_sca(
        self,
        sca_reference: str,
        customer_user_id: uuid.UUID,
        proposal_id: uuid.UUID,
        correlation_id: str,
        timeout_s: float
    ) -> bool:
        """
        Verify SCA reference against customer and proposal.
        
        Args:
            sca_reference: Opaque SCA reference from authentication boundary
            customer_user_id: Customer UUID
            proposal_id: Policy decision UUID
            correlation_id: Request correlation ID
            timeout_s: Timeout in seconds
        
        Returns:
            True if SCA completed and valid, False otherwise
        """
        req = AdapterRequest(
            payload={
                "sca_reference": sca_reference,
                "customer_token": str(customer_user_id),
                "proposal_id": str(proposal_id)
            },
            token_value=None,  # SCA verification doesn't use customer token
            correlation_id=correlation_id,
            timeout_s=timeout_s
        )
        
        result = self.call(req)
        return result.ok and result.payload and result.payload.get("valid", False)
    
    def call(self, req: AdapterRequest) -> AdapterResult:
        """Execute SCA verification through gateway."""
        gateway_resp = self.gateway.send(
            route="party.authentication.verify",
            payload=req.payload,
            token_value=req.token_value,
            correlation_id=req.correlation_id,
            timeout_s=req.timeout_s
        )
        
        if gateway_resp.ok:
            return AdapterResult(
                ok=True,
                payload=gateway_resp.payload,
                error_code=None,
                error_detail=None
            )
        
        # SCA verification failure never reveals why (security)
        return AdapterResult(
            ok=False,
            payload=None,
            error_code="sca_failed",
            error_detail="SCA verification failed"
        )

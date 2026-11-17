"""Transactions adapter (A1)."""
from app.adapters.base import AdapterBase, AdapterRequest, AdapterResult
from app.adapters.gateway_client import GatewayClient


class TransactionsAdapter(AdapterBase):
    """Adapter A1: Retrieve transactions."""
    name = "TransactionsAdapter"
    
    def __init__(self, gateway: GatewayClient):
        self.gateway = gateway
    
    def call(self, req: AdapterRequest) -> AdapterResult:
        """
        List transactions for given arrangement and date range.
        Normalizes gateway response to adapter result.
        """
        gateway_resp = self.gateway.send(
            route="transactions.retrieve",
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
        
        # Map HTTP status to error code
        if gateway_resp.status_code in (401, 403):
            error_code = "unauthorised"
        elif gateway_resp.status_code >= 500:
            error_code = "unavailable"
        else:
            error_code = "rejected"
        
        return AdapterResult(
            ok=False,
            payload=None,
            error_code=error_code,
            error_detail=gateway_resp.error_detail
        )

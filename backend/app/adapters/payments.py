"""Payments adapter (A6)."""
from app.adapters.base import AdapterBase, AdapterRequest, AdapterResult
from app.adapters.gateway_client import GatewayClient


class PaymentsAdapter(AdapterBase):
    """Adapter A6: Retry payment."""
    name = "PaymentsAdapter"
    
    def __init__(self, gateway: GatewayClient):
        self.gateway = gateway
    
    def call(self, req: AdapterRequest) -> AdapterResult:
        """Retry payment execution."""
        gateway_resp = self.gateway.send(
            route="payments.retry",
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

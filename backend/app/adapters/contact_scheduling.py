"""Contact scheduling adapter (A3)."""
from app.adapters.base import AdapterBase, AdapterRequest, AdapterResult
from app.adapters.gateway_client import GatewayClient


class ContactSchedulingAdapter(AdapterBase):
    """Adapter A3: Schedule callback (reserved, not called in this scope)."""
    name = "ContactSchedulingAdapter"
    
    def __init__(self, gateway: GatewayClient):
        self.gateway = gateway
    
    def call(self, req: AdapterRequest) -> AdapterResult:
        """
        Record callback preference.
        Not called in scope - T3 schedule_callback records path only.
        Interface exists for FR-011 future work.
        """
        # Placeholder - not called in this scope
        return AdapterResult(
            ok=True,
            payload={"preference_ref": "RESERVED"},
            error_code=None,
            error_detail=None
        )

"""Gateway client for LBG API gateway calls."""
from dataclasses import dataclass
from typing import Any
from app.core.clock import Clock


@dataclass
class GatewayResponse:
    """Normalized gateway response."""
    ok: bool
    status_code: int
    payload: dict[str, Any] | None
    error_code: str | None
    error_detail: str | None


class GatewayClient:
    """
    HTTP client wrapper for LBG API gateway calls.
    Attaches customer-scoped bearer token and correlation ID.
    """
    def __init__(self, base_url: str, clock: Clock):
        self.base_url = base_url
        self.clock = clock
    
    def send(
        self,
        route: str,
        payload: dict[str, Any],
        token_value: str | None,
        correlation_id: str,
        timeout_s: float
    ) -> GatewayResponse:
        """
        Send request to gateway.
        
        For demo/local: stub responses.
        In production: actual HTTP call with pooled httpx.Client.
        
        Args:
            route: Gateway route key
            payload: Request payload
            token_value: Customer-scoped token or None
            correlation_id: Request correlation ID
            timeout_s: Timeout in seconds
        
        Returns:
            GatewayResponse with normalized result
        """
        # Demo stub: always succeed with fixed responses
        # In production: httpx.Client.post with TLS, mTLS, retry policy
        
        if route == "transactions.retrieve":
            return GatewayResponse(
                ok=True,
                status_code=200,
                payload={
                    "items": [
                        {
                            "transaction_ref": "TXN-20261117-001",
                            "transaction_date": "2026-11-17T10:30:00Z",
                            "amount": 89.99,
                            "merchant_name": "Online Store XYZ",
                            "status": "completed"
                        }
                    ]
                },
                error_code=None,
                error_detail=None
            )
        
        elif route == "documents.request":
            return GatewayResponse(
                ok=True,
                status_code=200,
                payload={"document_request_ref": f"DOC-REQ-{correlation_id[:8]}"},
                error_code=None,
                error_detail=None
            )
        
        elif route == "card.controls.set":
            return GatewayResponse(
                ok=True,
                status_code=200,
                payload={
                    "card_state": payload["control_action"] + "d",  # "freezed" or "unfreezed"
                    "effective_at": self.clock.utc_now().isoformat() + "Z"
                },
                error_code=None,
                error_detail=None
            )
        
        elif route == "payments.retry":
            return GatewayResponse(
                ok=True,
                status_code=200,
                payload={
                    "payment_status": "submitted",
                    "submitted_at": self.clock.utc_now().isoformat() + "Z"
                },
                error_code=None,
                error_detail=None
            )
        
        elif route == "contact.handler.route":
            return GatewayResponse(
                ok=True,
                status_code=200,
                payload={
                    "queue_ref": "QUEUE-CARD-001",
                    "team_display": "Card and payments team",
                    "expected_by_at": self.clock.utc_now().isoformat() + "Z"
                },
                error_code=None,
                error_detail=None
            )
        
        elif route == "notify.send":
            return GatewayResponse(
                ok=True,
                status_code=200,
                payload={"provider_ref": f"NOTIF-{correlation_id[:8]}"},
                error_code=None,
                error_detail=None
            )
        
        elif route == "party.authentication.verify":
            # SCA verification - for demo always succeeds
            return GatewayResponse(
                ok=True,
                status_code=200,
                payload={"valid": True},
                error_code=None,
                error_detail=None
            )
        
        else:
            # Unknown route
            return GatewayResponse(
                ok=False,
                status_code=404,
                payload=None,
                error_code="not_found",
                error_detail=f"Unknown gateway route: {route}"
            )

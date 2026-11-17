"""Test adapters."""
from app.adapters.gateway_client import GatewayClient
from app.adapters.transactions import TransactionsAdapter
from app.adapters.card_controls import CardControlsAdapter
from app.adapters.routing import RoutingAdapter
from app.adapters.base import AdapterRequest
from app.core.clock import Clock


def test_transactions_adapter():
    """Test transactions adapter calls gateway."""
    clock = Clock()
    gateway = GatewayClient("http://demo", clock)
    adapter = TransactionsAdapter(gateway)
    
    req = AdapterRequest(
        payload={
            "arrangement_reference": "ACC-001",
            "from_date": "2026-11-01",
            "to_date": "2026-11-17"
        },
        token_value="demo-token",
        correlation_id="test-123",
        timeout_s=5.0
    )
    
    result = adapter.call(req)
    
    assert result.ok is True
    assert result.payload is not None
    assert "items" in result.payload


def test_card_controls_adapter():
    """Test card controls adapter."""
    clock = Clock()
    gateway = GatewayClient("http://demo", clock)
    adapter = CardControlsAdapter(gateway)
    
    req = AdapterRequest(
        payload={
            "card_token": "CARD-001",
            "control_action": "freeze",
            "sca_reference": "SCA-123"
        },
        token_value="demo-token",
        correlation_id="test-123",
        timeout_s=5.0
    )
    
    result = adapter.call(req)
    
    assert result.ok is True
    assert result.payload is not None


def test_routing_adapter():
    """Test routing adapter."""
    clock = Clock()
    gateway = GatewayClient("http://demo", clock)
    adapter = RoutingAdapter(gateway)
    
    req = AdapterRequest(
        payload={
            "case_ref": "CP-2026-001",
            "route_reason_code": "out_of_scope",
            "urgency": "standard",
            "vulnerability_flag": False
        },
        token_value="demo-token",
        correlation_id="test-123",
        timeout_s=5.0
    )
    
    result = adapter.call(req)
    
    assert result.ok is True
    assert result.payload is not None
    assert "queue_ref" in result.payload

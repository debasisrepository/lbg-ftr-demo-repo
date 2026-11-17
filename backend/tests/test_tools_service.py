"""Test tool layer."""
import uuid
from app.tools.token_issuer import ScopedTokenIssuer
from app.tools.layer import ToolLayer, ToolRequest
from app.core.clock import Clock
from app.core.context import RequestContext


def test_token_issuer():
    """Test scoped token issuance."""
    clock = Clock()
    issuer = ScopedTokenIssuer(clock)
    
    customer_id = uuid.uuid4()
    
    # Can issue token
    assert issuer.can_issue(customer_id) is True
    
    # Issue token
    handle = issuer.issue(customer_id, "test_scope", 120)
    
    assert handle.token_ref
    assert handle.scope_ref == "test_scope"
    assert handle.expires_at > clock.utc_now()
    
    # Retrieve token
    token = issuer.get_token(handle.token_ref)
    assert token is not None
    
    # Revoke token
    issuer.revoke(handle.token_ref)
    assert issuer.get_token(handle.token_ref) is None


def test_tool_layer_invoke():
    """Test tool invocation."""
    clock = Clock()
    issuer = ScopedTokenIssuer(clock)
    layer = ToolLayer(issuer, clock)
    
    req = ToolRequest(
        session_id=uuid.uuid4(),
        action_name="get_transactions",
        arguments={"arrangement_reference": "ACC-001"},
        decision_id=uuid.uuid4(),
        customer_user_id=uuid.uuid4()
    )
    
    # RequestContext uses static methods
    RequestContext.set_correlation_id("test-123")
    
    result = layer.invoke(req, None)  # ctx not used in demo implementation
    
    assert result.execution_mode == "executed"
    assert result.result is not None
    assert result.error_code is None

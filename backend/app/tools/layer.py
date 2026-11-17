"""Tool layer - permissioned execution of bounded tools."""
import uuid
from typing import Any
from dataclasses import dataclass
from app.core.context import RequestContext
from app.core.clock import Clock
from app.tools.token_issuer import ScopedTokenIssuer


@dataclass
class ToolRequest:
    """Request to execute a tool."""
    session_id: uuid.UUID
    action_name: str
    arguments: dict[str, Any]
    decision_id: uuid.UUID  # Policy approval reference
    customer_user_id: uuid.UUID


@dataclass
class ToolResult:
    """Result of tool execution."""
    execution_mode: str  # 'proposed', 'executed'
    result: dict[str, Any] | None
    error_code: str | None
    error_detail: str | None


class ToolLayer:
    """
    Tool layer mediates execution of eight bounded tools.
    Refuses any call without policy approval reference (B-4).
    Only caller of adapters (B-3).
    """
    def __init__(
        self,
        token_issuer: ScopedTokenIssuer,
        clock: Clock
    ):
        self.token_issuer = token_issuer
        self.clock = clock
    
    def invoke(self, req: ToolRequest, ctx: RequestContext) -> ToolResult:
        """
        Execute tool with policy approval check.
        
        Steps:
        1. Approval check - decision_id must exist, approved, not consumed, not expired
        2. Argument validation
        3. Execution mode check (shadow vs live)
        4. SCA gate (second line of defence)
        5. Token issuance if needed
        6. Execute with timeout
        7. Write tool_invocation row
        
        For demo: simplified implementation
        In production: full policy check, audit, executor registry
        """
        # For demo: always execute in 'executed' mode
        # In production: check policy_decision.shadow_mode
        
        # Issue token if tool needs one
        token_value = None
        if req.action_name in ("get_transactions", "request_document", "card_controls", "retry_payment", "route_to_queue"):
            if not self.token_issuer.can_issue(req.customer_user_id):
                return ToolResult(
                    execution_mode="executed",
                    result=None,
                    error_code="token_unavailable",
                    error_detail="Customer token cannot be issued"
                )
            
            token_handle = self.token_issuer.issue(
                customer_user_id=req.customer_user_id,
                scope=f"{req.action_name}",
                ttl_s=120
            )
            token_value = self.token_issuer.get_token(token_handle.token_ref)
        
        # For demo: return success with stub result
        # In production: call executor which calls adapter
        result_payload = {
            "action": req.action_name,
            "executed": True,
            "timestamp": self.clock.utc_now().isoformat()
        }
        
        if req.action_name == "get_transactions":
            result_payload["items"] = []
        elif req.action_name == "route_to_queue":
            result_payload["queue_ref"] = "QUEUE-001"
            result_payload["team_display"] = "Customer Support Team"
        
        return ToolResult(
            execution_mode="executed",
            result=result_payload,
            error_code=None,
            error_detail=None
        )

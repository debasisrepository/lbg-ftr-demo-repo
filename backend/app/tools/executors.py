"""Tool executors."""
from typing import Protocol
from dataclasses import dataclass
from app.adapters.base import AdapterRequest
from app.core.context import RequestContext


@dataclass
class ExecutorResult:
    """Result from tool executor."""
    ok: bool
    payload: dict | None
    error_code: str | None


class ToolExecutor(Protocol):
    """Protocol for tool executors."""
    def execute(self, args: dict, token_value: str | None, ctx: RequestContext) -> ExecutorResult:
        """Execute tool."""
        ...


class AdapterExecutor:
    """Generic adapter executor for tools that call adapters."""
    def __init__(self, adapter):
        self.adapter = adapter
    
    def execute(self, args: dict, token_value: str | None, ctx: RequestContext) -> ExecutorResult:
        """Execute adapter call."""
        req = AdapterRequest(
            payload=args,
            token_value=token_value,
            correlation_id=RequestContext.get_correlation_id(),
            timeout_s=5.0
        )
        result = self.adapter.call(req)
        return ExecutorResult(
            ok=result.ok,
            payload=result.payload,
            error_code=result.error_code
        )

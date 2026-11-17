"""Base adapter interface."""
from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Any


@dataclass
class AdapterRequest:
    """Adapter request with correlation and token."""
    payload: dict[str, Any]
    token_value: str | None
    correlation_id: str
    timeout_s: float


@dataclass
class AdapterResult:
    """Normalized adapter result."""
    ok: bool
    payload: dict[str, Any] | None
    error_code: str | None  # 'unauthorised', 'rejected', 'unavailable', 'timeout'
    error_detail: str | None


class AdapterBase(ABC):
    """Base class for all adapters."""
    name: str
    
    @abstractmethod
    def call(self, req: AdapterRequest) -> AdapterResult:
        """Execute adapter call and return normalized result."""
        pass

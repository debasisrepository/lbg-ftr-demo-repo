"""Health endpoint schemas."""
from datetime import datetime
from typing import List, Optional

from pydantic import BaseModel


class HealthResponse(BaseModel):
    """Health response."""
    status: str
    service: str
    version: str
    time: datetime


class HealthCheckSchema(BaseModel):
    """Health check schema."""
    name: str
    ok: bool
    informational: bool = False
    message: Optional[str] = None


class ReadinessResponse(BaseModel):
    """Readiness response."""
    status: str  # "ready" or "not_ready"
    checks: List[HealthCheckSchema]

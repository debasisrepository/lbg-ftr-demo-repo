"""Audit endpoint schemas."""
from datetime import datetime
from typing import List, Optional

from pydantic import BaseModel


class AuditEventItem(BaseModel):
    """Audit event item."""
    event_id: str
    event_type: str
    severity: str
    actor_user_id: Optional[str] = None
    actor_role_code: Optional[str] = None
    customer_account_id: Optional[str] = None
    affected_entity_type: Optional[str] = None
    affected_entity_id: Optional[str] = None
    correlation_id: str
    event_timestamp: datetime
    rationale_text: Optional[str] = None


class AuditEventListResponse(BaseModel):
    """Audit event list response."""
    items: List[AuditEventItem]
    total: int
    limit: int
    offset: int


# Legacy name for compatibility
AuditEventSchema = AuditEventItem

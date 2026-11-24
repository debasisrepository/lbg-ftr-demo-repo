"""Audit events router."""
from datetime import datetime
from typing import Optional

from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.core.clock import Clock
from app.core.context import RequestContext
from app.core.deps import get_db, get_clock, require_action
from app.schemas.audit_schemas import AuditEventListResponse
from app.repositories.audit_event_repository import AuditEventRepository


router = APIRouter(tags=["audit"])


@router.get("", response_model=AuditEventListResponse)
def list_audit_events(
    event_type: Optional[str] = Query(None),
    affected_entity_type: Optional[str] = Query(None),
    affected_entity_id: Optional[str] = Query(None),
    actor_user_id: Optional[str] = Query(None),
    customer_account_id: Optional[str] = Query(None),
    correlation_id: Optional[str] = Query(None),
    from_date: Optional[datetime] = Query(None, alias="from"),
    to_date: Optional[datetime] = Query(None, alias="to"),
    limit: int = Query(100, ge=1, le=100),
    offset: int = Query(0, ge=0),
    db: Session = Depends(get_db),
    clock: Clock = Depends(get_clock),
    ctx: RequestContext = require_action("audit.read"),
) -> AuditEventListResponse:
    """List audit events."""
    repo = AuditEventRepository(db)

    events, total = repo.list_events(
        event_type=event_type,
        affected_entity_type=affected_entity_type,
        affected_entity_id=affected_entity_id,
        actor_user_id=actor_user_id,
        customer_account_id=customer_account_id,
        correlation_id=correlation_id,
        from_date=from_date,
        to_date=to_date,
        limit=limit,
        offset=offset,
    )

    from app.schemas.audit_schemas import AuditEventItem

    items = [
        AuditEventItem(
            event_id=str(e.id),
            event_type=e.event_type,
            severity=e.severity,
            actor_user_id=str(e.actor_user_id) if e.actor_user_id else None,
            actor_role_code=e.actor_role_code,
            customer_account_id=str(e.customer_account_id) if e.customer_account_id else None,
            affected_entity_type=e.affected_entity_type,
            affected_entity_id=str(e.affected_entity_id) if e.affected_entity_id else None,
            correlation_id=e.correlation_id,
            event_timestamp=e.event_timestamp,
            rationale_text=e.rationale_text,
        )
        for e in events
    ]

    return AuditEventListResponse(items=items, total=total, limit=limit, offset=offset)

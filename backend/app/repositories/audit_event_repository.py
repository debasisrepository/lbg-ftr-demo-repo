"""Audit event repository."""
import uuid
from datetime import datetime
from typing import List, Optional

from sqlalchemy.orm import Session

from app.models.audit import AuditEvent


class AuditEventRepository:
    """Repository for audit event operations."""

    def __init__(self, db: Session):
        self.db = db

    def create(self, event: AuditEvent) -> AuditEvent:
        """Create audit event."""
        self.db.add(event)
        self.db.commit()
        self.db.refresh(event)
        return event

    def search(
        self,
        event_type: Optional[str] = None,
        actor_user_id: Optional[str] = None,
        correlation_id: Optional[str] = None,
        from_timestamp: Optional[datetime] = None,
        to_timestamp: Optional[datetime] = None,
        limit: int = 100,
        offset: int = 0,
    ) -> tuple[List[AuditEvent], int]:
        """Search audit events."""
        query = self.db.query(AuditEvent)

        if event_type:
            query = query.filter(AuditEvent.event_type == event_type)
        if actor_user_id:
            query = query.filter(AuditEvent.actor_user_id == actor_user_id)
        if correlation_id:
            query = query.filter(AuditEvent.correlation_id == correlation_id)
        if from_timestamp:
            query = query.filter(AuditEvent.event_timestamp >= from_timestamp)
        if to_timestamp:
            query = query.filter(AuditEvent.event_timestamp <= to_timestamp)

        total = query.count()

        events = (
            query.order_by(AuditEvent.event_timestamp.desc())
            .limit(limit)
            .offset(offset)
            .all()
        )

        return events, total

    def list_events(
        self,
        event_type: Optional[str] = None,
        affected_entity_type: Optional[str] = None,
        affected_entity_id: Optional[str] = None,
        actor_user_id: Optional[str] = None,
        customer_account_id: Optional[str] = None,
        correlation_id: Optional[str] = None,
        from_date: Optional[datetime] = None,
        to_date: Optional[datetime] = None,
        limit: int = 100,
        offset: int = 0,
    ) -> tuple[List[AuditEvent], int]:
        """List audit events with filters."""
        query = self.db.query(AuditEvent)

        if event_type:
            query = query.filter(AuditEvent.event_type == event_type)
        if affected_entity_type:
            query = query.filter(AuditEvent.affected_entity_type == affected_entity_type)
        if affected_entity_id:
            query = query.filter(AuditEvent.affected_entity_id == affected_entity_id)
        if actor_user_id:
            actor_uuid = uuid.UUID(actor_user_id) if isinstance(actor_user_id, str) else actor_user_id
            query = query.filter(AuditEvent.actor_user_id == actor_uuid)
        if customer_account_id:
            account_uuid = uuid.UUID(customer_account_id) if isinstance(customer_account_id, str) else customer_account_id
            query = query.filter(AuditEvent.customer_account_id == account_uuid)
        if correlation_id:
            query = query.filter(AuditEvent.correlation_id == correlation_id)
        if from_date:
            query = query.filter(AuditEvent.event_timestamp >= from_date)
        if to_date:
            query = query.filter(AuditEvent.event_timestamp <= to_date)

        total = query.count()
        events = query.order_by(AuditEvent.event_timestamp.desc()).limit(limit).offset(offset).all()

        return events, total

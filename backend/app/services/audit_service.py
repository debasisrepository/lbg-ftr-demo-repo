"""Audit service"""
import uuid
from datetime import datetime, timedelta

from sqlalchemy.orm import Session

from ..models.audit import AuditEvent
from ..repositories.audit_event_repository import AuditEventRepository


class AuditService:
    """Handles audit event recording"""

    def __init__(self, db: Session):
        self.db = db
        self.audit_event_repo = AuditEventRepository(db)

    def record_payment_event(
        self,
        customer_id: uuid.UUID,
        payment_order_id: uuid.UUID,
        event_type: str,
        outcome: str,
        correlation_id: str,
        actor_type: str = "customer",
        actor_id: str | None = None,
        severity: str = "info",
        detail_json: dict | None = None
    ) -> AuditEvent:
        """Record a payment-related audit event"""

        now = datetime.now(datetime.now().astimezone().tzinfo)
        retain_until = now + timedelta(days=365 * 7)  # 7 years retention

        audit_event = AuditEvent(
            audit_event_id=uuid.uuid4(),
            customer_id=customer_id,
            payment_order_id=payment_order_id,
            actor_type=actor_type,
            actor_id=actor_id or str(customer_id),
            event_type=event_type,
            event_category="payment",
            entity_type="payment_order",
            entity_id=str(payment_order_id),
            outcome=outcome,
            severity=severity,
            customer_ref=None,
            payment_ref=None,
            correlation_id=correlation_id,
            detail_json=detail_json,
            occurred_at=now,
            retain_until=retain_until,
            created_at=now
        )

        return self.audit_event_repo.create(audit_event)

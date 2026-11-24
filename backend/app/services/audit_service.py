"""Audit service."""
import uuid
from typing import Optional

from sqlalchemy.orm import Session

from app.core.clock import Clock
from app.core.logging import get_logger
from app.models.audit import AuditEvent
from app.repositories.audit_event_repository import AuditEventRepository

logger = get_logger(__name__)

# Forbidden fields that must never appear in audit payloads
FORBIDDEN_FIELDS = {"password", "token", "password_hash", "access_token", "credit_status_indicator"}


class AuditService:
    """Service for audit operations."""

    def __init__(self, db: Session, clock: Clock):
        self.db = db
        self.clock = clock
        self.repo = AuditEventRepository(db)

    def append(
        self,
        event_type: str,
        severity: str,
        correlation_id: str,
        actor_user_id: Optional[str] = None,
        actor_role_code: Optional[str] = None,
        customer_account_id: Optional[str] = None,
        affected_entity_type: Optional[str] = None,
        affected_entity_id: Optional[str] = None,
        rationale_text: Optional[str] = None,
        policy_evaluation_record_id: Optional[str] = None,
        event_payload_json: Optional[dict] = None,
    ) -> AuditEvent:
        """Append audit event.
        
        Args:
            event_type: Type of event
            severity: Severity level (info, warning, error, critical)
            correlation_id: Request correlation ID
            actor_user_id: Optional user who performed action
            actor_role_code: Optional role of actor
            customer_account_id: Optional customer account affected
            affected_entity_type: Optional entity type affected
            affected_entity_id: Optional entity ID affected
            rationale_text: Optional rationale
            policy_evaluation_record_id: Optional policy evaluation ID
            event_payload_json: Optional payload (sensitive fields removed)
            
        Returns:
            Created audit event
        """
        now = self.clock.now()

        # Guard against sensitive data in payload
        safe_payload = self._sanitize_payload(event_payload_json) if event_payload_json else None

        event = AuditEvent(
            id=uuid.uuid4(),
            created_at=now,
            updated_at=now,
            event_type=event_type,
            severity=severity,
            actor_user_id=uuid.UUID(actor_user_id) if actor_user_id else None,
            actor_role_code=actor_role_code,
            customer_account_id=uuid.UUID(customer_account_id) if customer_account_id else None,
            affected_entity_type=affected_entity_type,
            affected_entity_id=affected_entity_id,
            correlation_id=correlation_id,
            event_timestamp=now,
            rationale_text=rationale_text,
            policy_evaluation_record_id=uuid.UUID(policy_evaluation_record_id) if policy_evaluation_record_id else None,
            event_payload_json=safe_payload,
        )

        return self.repo.create(event)

    def _sanitize_payload(self, payload: dict) -> dict:
        """Remove forbidden fields from payload."""
        if not isinstance(payload, dict):
            return payload

        sanitized = {}
        for key, value in payload.items():
            if key.lower() in FORBIDDEN_FIELDS:
                logger.warning("audit_payload_contains_forbidden_field", field=key)
                continue

            if isinstance(value, dict):
                sanitized[key] = self._sanitize_payload(value)
            elif isinstance(value, list):
                sanitized[key] = [
                    self._sanitize_payload(item) if isinstance(item, dict) else item
                    for item in value
                ]
            else:
                sanitized[key] = value

        return sanitized

"""Audit service."""
import uuid
from datetime import datetime
from typing import Any

from app.core.clock import Clock
from app.models.audit import AuditEntry
from app.repositories.audit_repository import AuditRepository


class AuditService:
    """Service for recording audit entries."""
    
    def __init__(self, audit_repo: AuditRepository, clock: Clock):
        self.audit_repo = audit_repo
        self.clock = clock
    
    def record(
        self,
        correlation_id: str,
        audit_category: str,
        event_type: str,
        actor_type: str,
        actor_reference: str | None,
        entity_type: str | None,
        entity_id: str | None,
        severity: str = "info",
        metadata: dict[str, Any] | None = None,
        state_before_hash: str | None = None,
        state_after_hash: str | None = None
    ) -> AuditEntry:
        """Record an audit entry within a transaction."""
        entry = AuditEntry(
            id=uuid.uuid4(),
            correlation_id=correlation_id,
            audit_category=audit_category,
            event_type=event_type,
            actor_type=actor_type,
            actor_reference=actor_reference,
            entity_type=entity_type,
            entity_id=entity_id,
            severity=severity,
            metadata_json=metadata or {},
            state_before_hash=state_before_hash,
            state_after_hash=state_after_hash,
            created_at=self.clock.utcnow()
        )
        return self.audit_repo.add(entry)
    
    def record_isolated(
        self,
        correlation_id: str,
        audit_category: str,
        event_type: str,
        actor_type: str,
        actor_reference: str | None,
        entity_type: str | None,
        entity_id: str | None,
        severity: str = "info",
        metadata: dict[str, Any] | None = None
    ) -> AuditEntry:
        """Record an audit entry in an isolated transaction.
        
        Used for recording failures before raising exceptions.
        """
        # In a real implementation, this would use a separate session
        # For now, we use the same record method
        return self.record(
            correlation_id=correlation_id,
            audit_category=audit_category,
            event_type=event_type,
            actor_type=actor_type,
            actor_reference=actor_reference,
            entity_type=entity_type,
            entity_id=entity_id,
            severity=severity,
            metadata=metadata
        )

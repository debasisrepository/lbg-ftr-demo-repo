from datetime import datetime, timezone
from sqlalchemy.orm import Session
from app.models.audit import AuditLog
import json


class AuditRepository:
    """Repository for audit log database operations."""

    def __init__(self, db: Session):
        self.db = db

    def create_audit_log(
        self,
        correlation_id: str,
        auth_session_id: int | None,
        user_identity_id: int | None,
        entity_type: str | None,
        entity_id: str | None,
        event_type: str,
        severity: str,
        payload: dict | None = None
    ) -> AuditLog:
        """Create a new audit log entry."""
        now = datetime.now(timezone.utc)
        audit = AuditLog(
            correlation_id=correlation_id,
            auth_session_id=auth_session_id,
            user_identity_id=user_identity_id,
            entity_type=entity_type,
            entity_id=entity_id,
            event_type=event_type,
            severity=severity,
            payload_json=json.dumps(payload) if payload else None,
            occurred_at=now,
            created_at=now
        )
        self.db.add(audit)
        self.db.commit()
        self.db.refresh(audit)
        return audit

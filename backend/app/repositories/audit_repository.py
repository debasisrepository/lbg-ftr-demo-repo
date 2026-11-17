"""Audit repository."""
from sqlalchemy.orm import Session

from app.models.audit import AuditEntry


class AuditRepository:
    """Repository for audit entries."""

    def __init__(self, session: Session):
        self.session = session

    def add(self, entry: AuditEntry) -> AuditEntry:
        """Add an audit entry."""
        self.session.add(entry)
        self.session.flush()
        return entry

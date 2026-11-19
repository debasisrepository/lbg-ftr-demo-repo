"""AuditEvent repository"""
from sqlalchemy.orm import Session

from ..models.audit import AuditEvent


class AuditEventRepository:
    def __init__(self, db: Session):
        self.db = db

    def create(self, event: AuditEvent) -> AuditEvent:
        self.db.add(event)
        self.db.flush()
        return event

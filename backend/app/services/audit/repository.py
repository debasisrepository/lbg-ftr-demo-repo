from sqlalchemy import select, func
from sqlalchemy.orm import Session
import uuid
from app.core.clock import Clock
from app.core.ids import IdGenerator
from app.services.audit.models import AuditLogEntry


class AuditRepository:
    def __init__(self, db: Session):
        self.db = db

    def get_last_entry_in_chain(self, chain_key: str) -> AuditLogEntry | None:
        stmt = (
            select(AuditLogEntry)
            .where(AuditLogEntry.chain_key == chain_key)
            .order_by(AuditLogEntry.chain_seq.desc())
            .limit(1)
        )
        return self.db.execute(stmt).scalar_one_or_none()

    def create_entry(
        self,
        chain_key: str,
        chain_seq: int,
        actor_type: str,
        source_component: str,
        event_class: str,
        severity: str,
        entity_type: str,
        entity_id: str,
        outcome_code: str,
        summary_text: str,
        correlation_id: str,
        retention_class: str,
        previous_entry_hash: str | None,
        entry_hash: str,
        case_id: uuid.UUID | None = None,
        session_id: uuid.UUID | None = None,
        actor_user_id: int | None = None,
        actor_agent_code: str | None = None,
    ) -> AuditLogEntry:
        entry = AuditLogEntry(
            id=IdGenerator.uuid4(),
            chain_key=chain_key,
            chain_seq=chain_seq,
            actor_type=actor_type,
            case_id=case_id,
            session_id=session_id,
            actor_user_id=actor_user_id,
            actor_agent_code=actor_agent_code,
            source_component=source_component,
            event_class=event_class,
            severity=severity,
            entity_type=entity_type,
            entity_id=entity_id,
            outcome_code=outcome_code,
            summary_text=summary_text,
            correlation_id=correlation_id,
            retention_class=retention_class,
            previous_entry_hash=previous_entry_hash,
            entry_hash=entry_hash,
            occurred_at=Clock.utc_now(),
        )
        self.db.add(entry)
        return entry

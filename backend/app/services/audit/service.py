from sqlalchemy.orm import Session
import uuid
from app.core.clock import Clock
from app.services.audit.repository import AuditRepository
from app.services.audit.hashing import AuditHasher


class AuditService:
    def __init__(self, db: Session):
        self.db = db
        self.repo = AuditRepository(db)

    def record(
        self,
        chain_key: str,
        actor_type: str,
        source_component: str,
        event_class: str,
        entity_type: str,
        entity_id: str,
        outcome_code: str,
        summary_text: str,
        correlation_id: str,
        severity: str = "info",
        retention_class: str = "regulatory",
        case_id: uuid.UUID | None = None,
        session_id: uuid.UUID | None = None,
        actor_user_id: int | None = None,
        actor_agent_code: str | None = None,
    ):
        self.db.flush()
        last_entry = self.repo.get_last_entry_in_chain(chain_key)
        chain_seq = 1 if last_entry is None else last_entry.chain_seq + 1
        previous_hash = None if last_entry is None else last_entry.entry_hash

        occurred_at = Clock.utc_now()
        entry_hash = AuditHasher.compute_hash(
            chain_key=chain_key,
            chain_seq=chain_seq,
            actor_type=actor_type,
            source_component=source_component,
            event_class=event_class,
            entity_type=entity_type,
            entity_id=entity_id,
            outcome_code=outcome_code,
            summary_text=summary_text,
            occurred_at=occurred_at,
            previous_hash=previous_hash,
        )

        entry = self.repo.create_entry(
            chain_key=chain_key,
            chain_seq=chain_seq,
            actor_type=actor_type,
            source_component=source_component,
            event_class=event_class,
            severity=severity,
            entity_type=entity_type,
            entity_id=entity_id,
            outcome_code=outcome_code,
            summary_text=summary_text,
            correlation_id=correlation_id,
            retention_class=retention_class,
            previous_entry_hash=previous_hash,
            entry_hash=entry_hash,
            case_id=case_id,
            session_id=session_id,
            actor_user_id=actor_user_id,
            actor_agent_code=actor_agent_code,
        )
        self.db.flush()
        return entry

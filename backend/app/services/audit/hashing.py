import hashlib
from datetime import datetime


class AuditHasher:
    @staticmethod
    def compute_hash(
        chain_key: str,
        chain_seq: int,
        actor_type: str,
        source_component: str,
        event_class: str,
        entity_type: str,
        entity_id: str,
        outcome_code: str,
        summary_text: str,
        occurred_at: datetime,
        previous_hash: str | None,
    ) -> str:
        canonical_form = "|".join([
            previous_hash or "",
            chain_key,
            str(chain_seq),
            actor_type,
            source_component,
            event_class,
            entity_type,
            entity_id,
            outcome_code,
            summary_text[:500],
            occurred_at.isoformat(),
        ])
        return hashlib.sha256(canonical_form.encode("utf-8")).hexdigest()

import uuid
from app.services.audit.service import AuditService
from app.services.audit.repository import AuditRepository
from app.services.audit.hashing import AuditHasher


def test_audit_service_creates_entry_with_hash_chain(db_session):
    audit = AuditService(db_session)

    entry1 = audit.record(
        chain_key="test-chain",
        actor_type="system",
        source_component="test",
        event_class="case_created",
        entity_type="case",
        entity_id="case-1",
        outcome_code="success",
        summary_text="Case created",
        correlation_id="corr-1",
    )
    db_session.commit()

    assert entry1.chain_seq == 1
    assert entry1.previous_entry_hash is None
    assert entry1.entry_hash is not None
    assert len(entry1.entry_hash) == 64

    entry2 = audit.record(
        chain_key="test-chain",
        actor_type="system",
        source_component="test",
        event_class="case_updated",
        entity_type="case",
        entity_id="case-1",
        outcome_code="success",
        summary_text="Case updated",
        correlation_id="corr-2",
    )
    db_session.commit()

    assert entry2.chain_seq == 2
    assert entry2.previous_entry_hash == entry1.entry_hash
    assert entry2.entry_hash != entry1.entry_hash


def test_audit_hash_chain_integrity(db_session):
    audit = AuditService(db_session)

    entries = []
    for i in range(5):
        entry = audit.record(
            chain_key="integrity-chain",
            actor_type="system",
            source_component="test",
            event_class="test_event",
            entity_type="test",
            entity_id=f"entity-{i}",
            outcome_code="success",
            summary_text=f"Event {i}",
            correlation_id=f"corr-{i}",
        )
        entries.append(entry)
    db_session.commit()

    for i in range(1, len(entries)):
        assert entries[i].previous_entry_hash == entries[i-1].entry_hash
        assert entries[i].chain_seq == entries[i-1].chain_seq + 1
        assert len(entries[i].entry_hash) == 64


def test_audit_service_supports_different_actor_types(db_session):
    audit = AuditService(db_session)

    entry1 = audit.record(
        chain_key="actor-chain",
        actor_type="customer",
        actor_user_id=1,
        source_component="api",
        event_class="login",
        entity_type="user",
        entity_id="1",
        outcome_code="success",
        summary_text="User logged in",
        correlation_id="corr-1",
    )

    entry2 = audit.record(
        chain_key="actor-chain",
        actor_type="agent",
        actor_agent_code="intake_triage_agent",
        source_component="orchestrator",
        event_class="classification",
        entity_type="session",
        entity_id="sess-1",
        outcome_code="completed",
        summary_text="Issue classified",
        correlation_id="corr-2",
    )
    db_session.commit()

    assert entry1.actor_type == "customer"
    assert entry1.actor_user_id == 1
    assert entry2.actor_type == "agent"
    assert entry2.actor_agent_code == "intake_triage_agent"


def test_audit_repository_has_no_update_or_delete_methods(db_session):
    repo = AuditRepository(db_session)
    assert not hasattr(repo, "update_entry")
    assert not hasattr(repo, "delete_entry")

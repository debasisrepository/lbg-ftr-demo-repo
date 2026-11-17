"""Integration tests for return visit restoration."""
import uuid
from datetime import datetime, timezone

from app.core.clock import Clock
from app.models.audit import CaseEvent
from app.models.case import Case
from app.models.continuity import ContinuityContext
from app.models.ownership import CaseOwnership, ExpectedByCommitment
from app.repositories.audit_repository import AuditRepository
from app.repositories.case_repository import CaseRepository
from app.repositories.continuity_repository import ContinuityRepository
from app.repositories.history_repository import HistoryRepository
from app.repositories.ownership_repository import OwnershipRepository
from app.services.audit_service import AuditService
from app.services.continuity_service import ContinuityService


def test_restore_return_visit_integration(db_session):
    """Test full return visit restoration flow."""
    # Setup repositories and service
    case_repo = CaseRepository(db_session)
    continuity_repo = ContinuityRepository(db_session)
    ownership_repo = OwnershipRepository(db_session)
    history_repo = HistoryRepository(db_session)
    audit_repo = AuditRepository(db_session)
    audit_service = AuditService(audit_repo, Clock())
    
    service = ContinuityService(
        continuity_repo=continuity_repo,
        case_repo=case_repo,
        ownership_repo=ownership_repo,
        history_repo=history_repo,
        audit_repo=audit_repo,
        audit_service=audit_service,
        clock=Clock()
    )
    
    now = datetime.now(timezone.utc)
    case_id = uuid.uuid4()
    customer_party_id = "CUST-002"
    
    # Create case
    case = Case(
        id=case_id,
        case_reference="CP-INT001",
        customer_party_id=customer_party_id,
        brand="lloyds",
        issue_type="card_declined",
        classification_source="eligibility_rule",
        issue_title="Card Declined",
        issue_summary="Test integration case",
        origin_channel="mobile_app",
        current_lifecycle_state="under_review",
        current_status_code="reviewing",
        current_status_label="Under Review",
        opened_at=now,
        created_at=now,
        updated_at=now
    )
    db_session.add(case)
    
    # Create ownership
    ownership = CaseOwnership(
        id=uuid.uuid4(),
        case_id=case_id,
        owner_team_code="CARDS_DISPUTES",
        owner_semantic_label="Card Disputes Team",
        owner_display_name="Card Disputes",
        effective_from=now,
        is_current=True,
        created_at=now
    )
    db_session.add(ownership)
    
    # Create expected-by
    expected_by = ExpectedByCommitment(
        id=uuid.uuid4(),
        case_id=case_id,
        commitment_state="committed",
        expected_by_at=now,
        customer_explanatory_text="We'll update you by today",
        confidence_basis="colleague_set",
        effective_from=now,
        is_current=True,
        created_at=now
    )
    db_session.add(expected_by)
    
    # Create events
    event1 = CaseEvent(
        id=uuid.uuid4(),
        case_id=case_id,
        sequence_number=1,
        event_type="CaseCaptured",
        event_timestamp=now,
        summary_text="Case created",
        customer_visible_flag=True,
        actor_type="customer",
        correlation_id="test-001",
        created_at=now
    )
    db_session.add(event1)
    
    event2 = CaseEvent(
        id=uuid.uuid4(),
        case_id=case_id,
        sequence_number=2,
        event_type="CaseStatusChanged",
        event_timestamp=now,
        summary_text="Status changed to under review",
        customer_visible_flag=True,
        actor_type="system",
        correlation_id="test-002",
        created_at=now
    )
    db_session.add(event2)
    
    # Create continuity context
    context = ContinuityContext(
        id=uuid.uuid4(),
        case_id=case_id,
        package_version=3,
        structured_context_json={
            "case_reference": "CP-INT001",
            "issue_type": "card_declined"
        },
        llm_safe_payload_json={
            "case_reference": "CP-INT001"
        },
        colleague_payload_json={
            "case_reference": "CP-INT001"
        },
        restricted_fields_excluded_flag=True,
        last_channel="mobile_app",
        last_presented_at=now,
        effective_from=now,
        is_current=True,
        created_at=now
    )
    db_session.add(context)
    
    db_session.commit()
    
    # Execute return visit restoration
    result = service.restore_return_visit(
        case_reference="CP-INT001",
        return_session_token="valid-token-123",
        channel="mobile_app",
        correlation_id="test-return-visit-001"
    )
    
    # Verify result structure
    assert "case" in result
    assert "recent_updates" in result
    assert "context_version" in result
    assert "return_visit_restored_at" in result
    
    # Verify case detail
    assert result["case"].case_reference == "CP-INT001"
    assert result["case"].issue_type == "card_declined"
    assert result["case"].current_lifecycle_state == "under_review"
    
    # Verify context version
    assert result["context_version"] == 3
    
    # Verify recent updates (only customer-visible events)
    assert len(result["recent_updates"]) == 2
    assert result["recent_updates"][0]["event_type"] in ["CaseCaptured", "CaseStatusChanged"]
    assert result["recent_updates"][0]["customer_visible_flag"] is True
    
    # Verify audit entry was created
    from app.models.audit import AuditEntry
    from sqlalchemy import select
    
    audit_entries = db_session.scalars(
        select(AuditEntry).where(
            AuditEntry.entity_type == "case",
            AuditEntry.entity_id == str(case_id),
            AuditEntry.event_type == "return_visit_restored",
            AuditEntry.correlation_id == "test-return-visit-001"
        )
    ).all()
    assert len(audit_entries) == 1
    assert audit_entries[0].actor_type == "customer"
    assert audit_entries[0].audit_category == "access"


def test_restore_return_visit_no_existing_context(db_session):
    """Test return visit restoration when no continuity context exists."""
    # Setup repositories and service
    case_repo = CaseRepository(db_session)
    continuity_repo = ContinuityRepository(db_session)
    ownership_repo = OwnershipRepository(db_session)
    history_repo = HistoryRepository(db_session)
    audit_repo = AuditRepository(db_session)
    audit_service = AuditService(audit_repo, Clock())
    
    service = ContinuityService(
        continuity_repo=continuity_repo,
        case_repo=case_repo,
        ownership_repo=ownership_repo,
        history_repo=history_repo,
        audit_repo=audit_repo,
        audit_service=audit_service,
        clock=Clock()
    )
    
    now = datetime.now(timezone.utc)
    case_id = uuid.uuid4()
    customer_party_id = "CUST-002"  # Matches IdentityAdapter sandbox response
    
    # Create minimal case
    case = Case(
        id=case_id,
        case_reference="CP-INT002",
        customer_party_id=customer_party_id,
        brand="bank_of_scotland",
        issue_type="payment_missing",
        classification_source="eligibility_rule",
        issue_title="Payment Missing",
        issue_summary="Test case without context",
        origin_channel="chat",
        current_lifecycle_state="captured",
        current_status_code="received",
        current_status_label="Received",
        opened_at=now,
        created_at=now,
        updated_at=now
    )
    db_session.add(case)
    
    # Create ownership
    ownership = CaseOwnership(
        id=uuid.uuid4(),
        case_id=case_id,
        owner_team_code="INTAKE_DEFAULT",
        owner_semantic_label="Intake Team",
        owner_display_name="Intake & Triage",
        effective_from=now,
        is_current=True,
        created_at=now
    )
    db_session.add(ownership)
    
    # Create expected-by
    expected_by = ExpectedByCommitment(
        id=uuid.uuid4(),
        case_id=case_id,
        commitment_state="under_review",
        customer_explanatory_text="We're reviewing",
        confidence_basis="initial",
        effective_from=now,
        is_current=True,
        created_at=now
    )
    db_session.add(expected_by)
    
    db_session.commit()
    
    # Execute return visit restoration
    result = service.restore_return_visit(
        case_reference="CP-INT002",
        return_session_token="valid-token-456"
    )
    
    # Verify context_version defaults to 1 when no context exists
    assert result["context_version"] == 1
    assert result["recent_updates"] == []


def test_restore_return_visit_case_not_found(db_session):
    """Test return visit restoration with non-existent case."""
    from app.core.errors import NotFoundError
    import pytest
    
    # Setup repositories and service
    case_repo = CaseRepository(db_session)
    continuity_repo = ContinuityRepository(db_session)
    ownership_repo = OwnershipRepository(db_session)
    history_repo = HistoryRepository(db_session)
    audit_repo = AuditRepository(db_session)
    audit_service = AuditService(audit_repo, Clock())
    
    service = ContinuityService(
        continuity_repo=continuity_repo,
        case_repo=case_repo,
        ownership_repo=ownership_repo,
        history_repo=history_repo,
        audit_repo=audit_repo,
        audit_service=audit_service,
        clock=Clock()
    )
    
    # Attempt to restore non-existent case
    with pytest.raises(NotFoundError):
        service.restore_return_visit(
            case_reference="CP-NOTEXIST",
            return_session_token="valid-token-789"
        )


def test_restore_return_visit_invalid_token(db_session):
    """Test return visit restoration with invalid token."""
    import pytest
    
    # Setup repositories and service
    case_repo = CaseRepository(db_session)
    continuity_repo = ContinuityRepository(db_session)
    ownership_repo = OwnershipRepository(db_session)
    history_repo = HistoryRepository(db_session)
    audit_repo = AuditRepository(db_session)
    audit_service = AuditService(audit_repo, Clock())
    
    service = ContinuityService(
        continuity_repo=continuity_repo,
        case_repo=case_repo,
        ownership_repo=ownership_repo,
        history_repo=history_repo,
        audit_repo=audit_repo,
        audit_service=audit_service,
        clock=Clock()
    )
    
    # Attempt with empty token
    with pytest.raises(ValueError, match="Invalid return session token"):
        service.restore_return_visit(
            case_reference="CP-TEST",
            return_session_token=""
        )

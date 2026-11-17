"""Integration tests for continuity endpoints (service-level due to auth fixture issues)."""
import uuid
from datetime import datetime, timedelta, timezone

from app.core.clock import Clock
from app.models.case import Case, CaseStatusProjection
from app.models.continuity import ChannelHandoff, ContinuityContext
from app.models.ownership import CaseOwnership, ExpectedByCommitment
from app.repositories.audit_repository import AuditRepository
from app.repositories.case_repository import CaseRepository
from app.repositories.continuity_repository import ContinuityRepository
from app.repositories.history_repository import HistoryRepository
from app.repositories.ownership_repository import OwnershipRepository
from app.services.audit_service import AuditService
from app.services.continuity_service import ContinuityService


def test_get_continuity_package(db_session):
    """Test ContinuityService.get_package()."""
    now = datetime.now(timezone.utc)
    
    # Create a case
    case = Case(
        id=uuid.uuid4(),
        case_reference="CP-INTTEST1",
        customer_party_id="TEST-001",
        brand="lloyds",
        issue_type="card_declined",
        classification_source="eligibility_rule",
        issue_title="Card Declined",
        issue_summary="My card was declined",
        origin_channel="mobile_app",
        current_lifecycle_state="case_created",
        current_status_code="received",
        current_status_label="Received",
        continuity_state="current",
        opened_at=now,
        created_at=now,
        updated_at=now
    )
    db_session.add(case)
    
    # Create status projection
    projection = CaseStatusProjection(
        id=uuid.uuid4(),
        case_id=case.id,
        status_code="received",
        status_label="Received",
        lifecycle_state="case_created",
        status_icon="in_progress",
        status_color="blue",
        customer_facing_text="Your case has been received",
        next_step_text="We're reviewing your case",
        effective_from=now,
        is_current=True,
        created_at=now
    )
    db_session.add(projection)
    
    # Create ownership
    ownership = CaseOwnership(
        id=uuid.uuid4(),
        case_id=case.id,
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
        case_id=case.id,
        commitment_state="committed",
        expected_by_at=now + timedelta(days=3),
        customer_explanatory_text="We'll resolve this by",
        confidence_basis="team_capacity",
        effective_from=now,
        is_current=True,
        created_at=now
    )
    db_session.add(expected_by)
    
    # Create continuity context
    context = ContinuityContext(
        id=uuid.uuid4(),
        case_id=case.id,
        package_version=1,
        structured_context_json={
            "case_reference": "CP-INTTEST1",
            "customer_party_id": "TEST-001",
            "issue_type": "card_declined",
            "current_state": "case_created"
        },
        llm_safe_payload_json={},
        colleague_payload_json={},
        restricted_fields_excluded_flag=True,
        effective_from=now,
        is_current=True,
        created_at=now
    )
    db_session.add(context)
    db_session.commit()
    
    # Get package via service
    continuity_service = ContinuityService(
        continuity_repo=ContinuityRepository(db_session),
        case_repo=CaseRepository(db_session),
        ownership_repo=OwnershipRepository(db_session),
        history_repo=HistoryRepository(db_session),
        audit_repo=AuditRepository(db_session),
        audit_service=AuditService(AuditRepository(db_session), Clock()),
        clock=Clock()
    )
    
    package = continuity_service.get_package(case.case_reference, "TEST-001")
    
    assert package["context_version"] == 1
    assert package["customer_issue_summary"] == "My card was declined"
    assert "structured_context" in package
    assert "current_state" in package


def test_get_continuity_package_not_found(db_session):
    """Test get_package() with non-existent case."""
    from app.core.errors import NotFoundError
    import pytest
    
    continuity_service = ContinuityService(
        continuity_repo=ContinuityRepository(db_session),
        case_repo=CaseRepository(db_session),
        ownership_repo=OwnershipRepository(db_session),
        history_repo=HistoryRepository(db_session),
        audit_repo=AuditRepository(db_session),
        audit_service=AuditService(AuditRepository(db_session), Clock()),
        clock=Clock()
    )
    
    with pytest.raises(NotFoundError, match="Case CP-NOTEXIST not found"):
        continuity_service.get_package("CP-NOTEXIST", "TEST-001")


def test_record_handoff(db_session):
    """Test ContinuityService.record_handoff()."""
    now = datetime.now(timezone.utc)
    
    # Create a case
    case = Case(
        id=uuid.uuid4(),
        case_reference="CP-INTTEST2",
        customer_party_id="TEST-001",
        brand="lloyds",
        issue_type="card_declined",
        classification_source="eligibility_rule",
        issue_title="Card Declined",
        issue_summary="My card was declined",
        origin_channel="mobile_app",
        current_lifecycle_state="case_created",
        current_status_code="received",
        current_status_label="Received",
        continuity_state="current",
        opened_at=now,
        created_at=now,
        updated_at=now
    )
    db_session.add(case)
    db_session.commit()
    
    # Record handoff via service
    continuity_service = ContinuityService(
        continuity_repo=ContinuityRepository(db_session),
        case_repo=CaseRepository(db_session),
        ownership_repo=OwnershipRepository(db_session),
        history_repo=HistoryRepository(db_session),
        audit_repo=AuditRepository(db_session),
        audit_service=AuditService(AuditRepository(db_session), Clock()),
        clock=Clock()
    )
    
    continuity_service.record_handoff(
        case_reference=case.case_reference,
        customer_party_id="TEST-001",
        from_channel="mobile_app",
        to_channel="chat",
        context_presented_flag=True,
        correlation_id="test-001"
    )
    
    db_session.commit()
    
    # Verify case state updated
    db_session.refresh(case)
    assert case.continuity_state == "refresh_pending"


def test_list_colleague_cases(db_session):
    """Test ContinuityService.list_colleague_cases()."""
    now = datetime.now(timezone.utc)
    
    # Create 2 cases for CUST-002
    case1 = Case(
        id=uuid.uuid4(),
        case_reference="CP-COLL1",
        customer_party_id="CUST-002",
        brand="lloyds",
        issue_type="card_declined",
        classification_source="eligibility_rule",
        issue_title="Card Declined",
        issue_summary="Card declined",
        origin_channel="mobile_app",
        current_lifecycle_state="case_created",
        current_status_code="received",
        current_status_label="Received",
        opened_at=now,
        created_at=now,
        updated_at=now
    )
    db_session.add(case1)
    
    case2 = Case(
        id=uuid.uuid4(),
        case_reference="CP-COLL2",
        customer_party_id="CUST-002",
        brand="lloyds",
        issue_type="payment_missing",
        classification_source="eligibility_rule",
        issue_title="Payment Missing",
        issue_summary="Payment missing",
        origin_channel="mobile_app",
        current_lifecycle_state="case_created",
        current_status_code="received",
        current_status_label="Received",
        opened_at=now,
        created_at=now,
        updated_at=now
    )
    db_session.add(case2)
    db_session.commit()
    
    # List via service
    continuity_service = ContinuityService(
        continuity_repo=ContinuityRepository(db_session),
        case_repo=CaseRepository(db_session),
        ownership_repo=OwnershipRepository(db_session),
        history_repo=HistoryRepository(db_session),
        audit_repo=AuditRepository(db_session),
        audit_service=AuditService(AuditRepository(db_session), Clock()),
        clock=Clock()
    )
    
    summaries, total = continuity_service.list_colleague_cases(
        customer_party_id="CUST-002",
        limit=20,
        offset=0
    )
    
    assert total == 2
    assert len(summaries) == 2


def test_get_colleague_case(db_session):
    """Test ContinuityService.colleague_retrieve()."""
    now = datetime.now(timezone.utc)
    
    # Create a case
    case = Case(
        id=uuid.uuid4(),
        case_reference="CP-COLL3",
        customer_party_id="CUST-002",
        brand="lloyds",
        issue_type="card_declined",
        classification_source="eligibility_rule",
        issue_title="Card Declined",
        issue_summary="Card declined",
        origin_channel="mobile_app",
        current_lifecycle_state="case_created",
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
        case_id=case.id,
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
        case_id=case.id,
        commitment_state="committed",
        expected_by_at=now + timedelta(days=3),
        customer_explanatory_text="We'll resolve this by",
        confidence_basis="team_capacity",
        effective_from=now,
        is_current=True,
        created_at=now
    )
    db_session.add(expected_by)
    db_session.commit()
    
    # Retrieve via service
    continuity_service = ContinuityService(
        continuity_repo=ContinuityRepository(db_session),
        case_repo=CaseRepository(db_session),
        ownership_repo=OwnershipRepository(db_session),
        history_repo=HistoryRepository(db_session),
        audit_repo=AuditRepository(db_session),
        audit_service=AuditService(AuditRepository(db_session), Clock()),
        clock=Clock()
    )
    
    package = continuity_service.colleague_retrieve(
        case_reference=case.case_reference,
        colleague_reference="COLL-001",
        correlation_id="test-001"
    )
    
    assert package["case_reference"] == "CP-COLL3"
    assert package["customer_party_id"] == "CUST-002"
    assert package["issue_type"] == "card_declined"

"""Acceptance tests for cross-channel continuity (FR-013, FR-015)."""
import uuid
from datetime import datetime, timedelta, timezone

from app.core.clock import Clock
from app.models.audit import CaseEvent
from app.models.case import Case, CaseAnchorLink, CaseStatusProjection
from app.models.continuity import ChannelHandoff, ContinuityContext
from app.models.ownership import CaseOwnership, ExpectedByCommitment
from app.repositories.case_repository import CaseRepository
from app.repositories.continuity_repository import ContinuityRepository
from app.repositories.history_repository import HistoryRepository
from app.repositories.ownership_repository import OwnershipRepository
from app.services.continuity_service import ContinuityService
from app.services.audit_service import AuditService
from app.repositories.audit_repository import AuditRepository


def test_case_initiated_in_one_channel_can_be_retrieved_in_another(db_session):
    """
    A Case initiated or updated in one channel can be retrieved in another 
    supported channel for the same authenticated customer.
    """
    now = Clock.utcnow()
    
    # Create a case initiated in mobile_app
    case = Case(
        id=uuid.uuid4(),
        case_reference="CP-ACC1",
        customer_party_id="CUST-001",
        brand="lloyds",
        issue_type="card_declined",
        classification_source="eligibility_rule",
        issue_title="Card Declined",
        issue_summary="Card was declined at store",
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
    
    # Add required data
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
    
    expected_by = ExpectedByCommitment(
        id=uuid.uuid4(),
        case_id=case.id,
        commitment_state="committed",
        expected_by_at=now + timedelta(days=3),
        customer_explanatory_text="We'll resolve this soon",
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
            "case_reference": "CP-ACC1",
            "customer_party_id": "CUST-001",
            "issue_type": "card_declined",
            "current_state": "case_created"
        },
        llm_safe_payload_json={},
        colleague_payload_json={},
        restricted_fields_excluded_flag=True,
        last_channel="mobile_app",
        effective_from=now,
        is_current=True,
        created_at=now
    )
    db_session.add(context)
    db_session.commit()
    
    # Retrieve from chat channel (different channel)
    continuity_service = ContinuityService(
        continuity_repo=ContinuityRepository(db_session),
        case_repo=CaseRepository(db_session),
        ownership_repo=OwnershipRepository(db_session),
        history_repo=HistoryRepository(db_session),
        audit_repo=AuditRepository(db_session),
        audit_service=AuditService(AuditRepository(db_session), Clock()),
        clock=Clock()
    )
    
    package = continuity_service.get_package("CP-ACC1", "CUST-001")
    
    # Verify continuity package retrieved successfully
    assert package is not None
    assert package["context_version"] == 1
    assert package["customer_issue_summary"] == "Card was declined at store"
    assert "structured_context" in package


def test_channel_change_does_not_create_duplicate_case(db_session):
    """
    Channel change does not force creation of a duplicate Case for the 
    same in-scope issue unless explicitly required by business rules.
    """
    now = Clock.utcnow()
    
    # Create initial case
    case = Case(
        id=uuid.uuid4(),
        case_reference="CP-ACC2",
        customer_party_id="CUST-001",
        brand="lloyds",
        issue_type="card_declined",
        classification_source="eligibility_rule",
        issue_title="Card Declined",
        issue_summary="Card was declined",
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
    
    # Record handoff to chat
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
        case_reference="CP-ACC2",
        customer_party_id="CUST-001",
        from_channel="mobile_app",
        to_channel="chat",
        context_presented_flag=True,
        correlation_id="test-001"
    )
    db_session.commit()
    
    # Verify only one case exists
    case_repo = CaseRepository(db_session)
    cases, total = case_repo.list_for_customer("CUST-001", include_closed=True)
    assert total == 1
    assert cases[0].case_reference == "CP-ACC2"


def test_receiving_channel_can_access_approved_continuity_context(db_session):
    """
    The receiving channel can access the approved continuity context 
    needed to proceed.
    """
    now = Clock.utcnow()
    
    # Create case with continuity context
    case = Case(
        id=uuid.uuid4(),
        case_reference="CP-ACC3",
        customer_party_id="CUST-001",
        brand="lloyds",
        issue_type="card_declined",
        classification_source="eligibility_rule",
        issue_title="Card Declined",
        issue_summary="Card declined",
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
    
    # Create required data
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
    
    expected_by = ExpectedByCommitment(
        id=uuid.uuid4(),
        case_id=case.id,
        commitment_state="committed",
        expected_by_at=now + timedelta(days=3),
        customer_explanatory_text="We'll resolve this soon",
        confidence_basis="team_capacity",
        effective_from=now,
        is_current=True,
        created_at=now
    )
    db_session.add(expected_by)
    
    # Create approved continuity context
    context = ContinuityContext(
        id=uuid.uuid4(),
        case_id=case.id,
        package_version=1,
        structured_context_json={
            "case_reference": "CP-ACC3",
            "customer_party_id": "CUST-001",
            "issue_type": "card_declined",
            "issue_title": "Card Declined",
            "current_state": "case_created",
            "owner_team_code": "CARDS_DISPUTES",
            "expected_by_at": (now + timedelta(days=3)).isoformat()
        },
        llm_safe_payload_json={},
        colleague_payload_json={},
        restricted_fields_excluded_flag=True,
        last_channel="mobile_app",
        effective_from=now,
        is_current=True,
        created_at=now
    )
    db_session.add(context)
    db_session.commit()
    
    # Access continuity package
    continuity_service = ContinuityService(
        continuity_repo=ContinuityRepository(db_session),
        case_repo=CaseRepository(db_session),
        ownership_repo=OwnershipRepository(db_session),
        history_repo=HistoryRepository(db_session),
        audit_repo=AuditRepository(db_session),
        audit_service=AuditService(AuditRepository(db_session), Clock()),
        clock=Clock()
    )
    
    package = continuity_service.get_package("CP-ACC3", "CUST-001")
    
    # Verify context contains required fields
    assert "structured_context" in package
    assert package["structured_context"]["case_reference"] == "CP-ACC3"
    assert package["structured_context"]["owner_team_code"] == "CARDS_DISPUTES"
    assert "expected_by_at" in package["structured_context"]


def test_authorized_colleagues_can_retrieve_active_case(db_session):
    """
    Authorized colleagues can retrieve the active Case using customer 
    identity and case context.
    """
    now = Clock.utcnow()
    
    # Create case
    case = Case(
        id=uuid.uuid4(),
        case_reference="CP-ACC4",
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
    
    # Add required data
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
    
    expected_by = ExpectedByCommitment(
        id=uuid.uuid4(),
        case_id=case.id,
        commitment_state="committed",
        expected_by_at=now + timedelta(days=3),
        customer_explanatory_text="We'll resolve this soon",
        confidence_basis="team_capacity",
        effective_from=now,
        is_current=True,
        created_at=now
    )
    db_session.add(expected_by)
    db_session.commit()
    
    # Colleague retrieves case
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
        case_reference="CP-ACC4",
        colleague_reference="COLL-001",
        correlation_id="test-002"
    )
    
    # Verify colleague can access case
    assert package is not None
    assert package["case_reference"] == "CP-ACC4"
    assert package["customer_party_id"] == "CUST-002"


def test_retrieved_context_includes_latest_approved_status(db_session):
    """
    The retrieved context includes the latest approved status, owner, 
    expected-by date, and recent update history.
    """
    now = Clock.utcnow()
    
    # Create case with history
    case = Case(
        id=uuid.uuid4(),
        case_reference="CP-ACC5",
        customer_party_id="CUST-001",
        brand="lloyds",
        issue_type="card_declined",
        classification_source="eligibility_rule",
        issue_title="Card Declined",
        issue_summary="Card declined",
        origin_channel="mobile_app",
        current_lifecycle_state="in_progress",
        current_status_code="investigating",
        current_status_label="Investigating",
        latest_meaningful_update_at=now,
        opened_at=now - timedelta(hours=2),
        created_at=now - timedelta(hours=2),
        updated_at=now
    )
    db_session.add(case)
    
    # Add current ownership
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
    
    # Add current expected-by
    expected_by = ExpectedByCommitment(
        id=uuid.uuid4(),
        case_id=case.id,
        commitment_state="committed",
        expected_by_at=now + timedelta(days=3),
        customer_explanatory_text="Expected resolution date",
        confidence_basis="team_capacity",
        effective_from=now,
        is_current=True,
        created_at=now
    )
    db_session.add(expected_by)
    
    # Add recent events
    event1 = CaseEvent(
        id=uuid.uuid4(),
        case_id=case.id,
        sequence_number=1,
        event_type="CaseCaptured",
        event_timestamp=now - timedelta(hours=2),
        summary_text="Case created",
        customer_visible_flag=True,
        actor_type="customer",
        correlation_id="test-003",
        created_at=now - timedelta(hours=2)
    )
    db_session.add(event1)
    
    event2 = CaseEvent(
        id=uuid.uuid4(),
        case_id=case.id,
        sequence_number=2,
        event_type="CaseStatusChanged",
        event_timestamp=now,
        summary_text="Status changed to investigating",
        customer_visible_flag=True,
        actor_type="colleague",
        correlation_id="test-004",
        created_at=now
    )
    db_session.add(event2)
    
    # Create continuity context
    context = ContinuityContext(
        id=uuid.uuid4(),
        case_id=case.id,
        package_version=1,
        structured_context_json={
            "case_reference": "CP-ACC5",
            "current_lifecycle_state": "in_progress",
            "current_status_code": "investigating",
            "owner_team_code": "CARDS_DISPUTES",
            "expected_by_at": (now + timedelta(days=3)).isoformat(),
            "latest_update_text": "We're investigating your case",
            "recent_events": ["CaseCaptured", "CaseStatusChanged"]
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
    
    # Retrieve package
    continuity_service = ContinuityService(
        continuity_repo=ContinuityRepository(db_session),
        case_repo=CaseRepository(db_session),
        ownership_repo=OwnershipRepository(db_session),
        history_repo=HistoryRepository(db_session),
        audit_repo=AuditRepository(db_session),
        audit_service=AuditService(AuditRepository(db_session), Clock()),
        clock=Clock()
    )
    
    package = continuity_service.get_package("CP-ACC5", "CUST-001")
    
    # Verify package includes all required elements
    assert package["current_state"] == "in_progress"
    structured = package["structured_context"]
    assert structured["current_status_code"] == "investigating"
    assert structured["owner_team_code"] == "CARDS_DISPUTES"
    assert "expected_by_at" in structured
    assert "recent_events" in structured

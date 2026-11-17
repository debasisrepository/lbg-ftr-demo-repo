"""Integration tests for case creation with real database."""
import pytest
from sqlalchemy import select

from app.models.audit import CaseEvent
from app.models.case import Case, CaseAnchorLink, CaseStatusProjection
from app.models.ownership import CaseOwnership, ExpectedByCommitment
from app.schemas.case import CaseCreateRequest
from app.adapters.customer_case_adapter import CustomerCaseAdapter
from app.core.clock import Clock
from app.repositories.audit_repository import AuditRepository
from app.repositories.case_repository import CaseRepository
from app.repositories.config_repository import ConfigRepository
from app.repositories.history_repository import HistoryRepository
from app.repositories.ownership_repository import OwnershipRepository
from app.services.audit_service import AuditService
from app.services.case_service import CaseService
from app.services.policy_service import PolicyService


@pytest.fixture
def case_service(db_session):
    """Create case service with real repositories."""
    from app.models.config import IssueEligibilityRule, OwnerTeamMapping
    import uuid
    from datetime import datetime, timezone
    
    # Seed eligibility rules for tests
    now = datetime.now(timezone.utc)
    rules = [
        IssueEligibilityRule(
            id=uuid.uuid4(),
            issue_type="card_declined",
            is_eligible=True,
            priority_weight=100,
            created_at=now
        ),
        IssueEligibilityRule(
            id=uuid.uuid4(),
            issue_type="payment_missing",
            is_eligible=True,
            priority_weight=90,
            created_at=now
        ),
        IssueEligibilityRule(
            id=uuid.uuid4(),
            issue_type="general_query",
            is_eligible=False,
            redirect_journey_code="existing_support",
            priority_weight=50,
            created_at=now
        ),
    ]
    for rule in rules:
        db_session.add(rule)
    
    # Seed owner mapping
    owner_mapping = OwnerTeamMapping(
        id=uuid.uuid4(),
        owner_team_code="INTAKE_DEFAULT",
        owner_semantic_label="Intake Team",
        owner_display_name="Intake & Triage",
        is_active=True,
        created_at=now
    )
    db_session.add(owner_mapping)
    db_session.commit()
    
    case_repo = CaseRepository(db_session)
    history_repo = HistoryRepository(db_session)
    ownership_repo = OwnershipRepository(db_session)
    config_repo = ConfigRepository(db_session)
    audit_repo = AuditRepository(db_session)
    
    policy_service = PolicyService(config_repo)
    audit_service = AuditService(audit_repo, Clock())
    customer_case_adapter = CustomerCaseAdapter()
    
    return CaseService(
        case_repo=case_repo,
        history_repo=history_repo,
        ownership_repo=ownership_repo,
        config_repo=config_repo,
        audit_repo=audit_repo,
        policy_service=policy_service,
        audit_service=audit_service,
        customer_case_adapter=customer_case_adapter,
        clock=Clock()
    )


def test_create_case_persists_all_components(case_service, db_session):
    """Test that case creation persists case, anchor, projection, ownership, expected-by, and event."""
    # Setup
    request = CaseCreateRequest(
        issue_type="card_declined",
        issue_summary="My card was declined at the store",
        origin_channel="mobile_app"
    )
    
    # Execute
    result = case_service.create_case(
        principal_customer_party_id="CUST-TEST",
        principal_brand="lloyds",
        request=request,
        correlation_id="test-int-001"
    )
    db_session.commit()
    
    # Assert outcome
    assert result.outcome == "created"
    assert result.case is not None
    case_reference = result.case.case_reference
    
    # Verify case persisted
    case = db_session.scalar(select(Case).where(Case.case_reference == case_reference))
    assert case is not None
    assert case.customer_party_id == "CUST-TEST"
    assert case.issue_type == "card_declined"
    assert case.current_lifecycle_state == "case_created"
    
    # Verify anchor link persisted
    anchor = db_session.scalar(select(CaseAnchorLink).where(CaseAnchorLink.case_id == case.id))
    assert anchor is not None
    assert anchor.anchor_domain == "customer_case"
    assert anchor.link_status == "active"
    
    # Verify projection persisted
    projection = db_session.scalar(
        select(CaseStatusProjection).where(
            CaseStatusProjection.case_id == case.id,
            CaseStatusProjection.is_current == True  # noqa: E712
        )
    )
    assert projection is not None
    assert projection.status_code == "received"
    assert projection.lifecycle_state == "case_created"
    
    # Verify ownership persisted
    ownership = db_session.scalar(
        select(CaseOwnership).where(
            CaseOwnership.case_id == case.id,
            CaseOwnership.is_current == True  # noqa: E712
        )
    )
    assert ownership is not None
    assert ownership.owner_team_code == "INTAKE_DEFAULT"
    
    # Verify expected-by persisted
    expected_by = db_session.scalar(
        select(ExpectedByCommitment).where(
            ExpectedByCommitment.case_id == case.id,
            ExpectedByCommitment.is_current == True  # noqa: E712
        )
    )
    assert expected_by is not None
    assert expected_by.commitment_state == "under_review"
    
    # Verify event persisted
    event = db_session.scalar(
        select(CaseEvent).where(CaseEvent.case_id == case.id)
    )
    assert event is not None
    assert event.event_type == "CaseCaptured"
    assert event.sequence_number == 1


def test_create_case_surfaces_existing_open_case(case_service, db_session):
    """Test that creating a case with same issue_type returns existing open case."""
    # Setup - create first case
    request = CaseCreateRequest(
        issue_type="payment_missing",
        issue_summary="My payment is missing",
        origin_channel="mobile_app"
    )
    
    first_result = case_service.create_case(
        principal_customer_party_id="CUST-TEST-2",
        principal_brand="lloyds",
        request=request,
        correlation_id="test-int-002a"
    )
    db_session.commit()
    
    assert first_result.outcome == "created"
    first_reference = first_result.case.case_reference
    
    # Execute - try to create another case with same issue_type
    second_result = case_service.create_case(
        principal_customer_party_id="CUST-TEST-2",
        principal_brand="lloyds",
        request=request,
        correlation_id="test-int-002b"
    )
    
    # Assert - should surface existing case, not create new one
    assert second_result.outcome == "surfaced"
    assert second_result.case.case_reference == first_reference
    
    # Verify only one case exists
    cases = list(db_session.scalars(
        select(Case).where(
            Case.customer_party_id == "CUST-TEST-2",
            Case.issue_type == "payment_missing"
        )
    ))
    assert len(cases) == 1


def test_create_case_returns_not_eligible_for_ineligible_issue_type(case_service, db_session):
    """Test that ineligible issue types return not_eligible outcome."""
    # Setup
    request = CaseCreateRequest(
        issue_type="general_query",
        issue_summary="I have a general question",
        origin_channel="mobile_app"
    )
    
    # Execute
    result = case_service.create_case(
        principal_customer_party_id="CUST-TEST-3",
        principal_brand="lloyds",
        request=request,
        correlation_id="test-int-003"
    )
    
    # Assert
    assert result.outcome == "not_eligible"
    assert result.case is None
    assert result.redirect_journey_code == "existing_support"
    
    # Verify no case was created
    cases = list(db_session.scalars(
        select(Case).where(
            Case.customer_party_id == "CUST-TEST-3",
            Case.issue_type == "general_query"
        )
    ))
    assert len(cases) == 0


def test_get_case_retrieves_case_with_projections(case_service, db_session):
    """Test that get_case retrieves case with all projections."""
    # Setup - create a case
    request = CaseCreateRequest(
        issue_type="card_declined",
        issue_summary="Card declined issue",
        origin_channel="mobile_app"
    )
    
    create_result = case_service.create_case(
        principal_customer_party_id="CUST-TEST-4",
        principal_brand="lloyds",
        request=request,
        correlation_id="test-int-004"
    )
    db_session.commit()
    
    case_reference = create_result.case.case_reference
    
    # Execute
    result = case_service.get_case(
        customer_party_id="CUST-TEST-4",
        case_reference=case_reference
    )
    
    # Assert
    assert result.case_reference == case_reference
    assert result.customer_party_id == "CUST-TEST-4"
    assert result.issue_type == "card_declined"
    assert result.status_code == "received"
    assert result.owner.owner_type == "team"
    assert result.owner.owner_semantic_label == "Intake Team"
    assert result.expected_by.commitment_state == "under_review"

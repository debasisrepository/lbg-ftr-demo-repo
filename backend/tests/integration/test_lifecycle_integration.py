"""Integration tests for lifecycle transitions."""
import os
import uuid
from datetime import datetime

import pytest
from sqlalchemy.orm import Session

from app.adapters.customer_case_adapter import CustomerCaseAdapter
from app.core.clock import Clock
from app.core.lifecycle_graph import LifecycleGraph
from app.models.audit import CaseEvent
from app.models.case import Case, CaseAnchorLink, CaseStatusProjection
from app.models.config import CaseLifecycleTransition, IssueEligibilityRule, OwnerTeamMapping
from app.models.ownership import CaseOwnership, ExpectedByCommitment
from app.repositories.audit_repository import AuditRepository
from app.repositories.case_repository import CaseRepository
from app.repositories.config_repository import ConfigRepository
from app.repositories.history_repository import HistoryRepository
from app.repositories.ownership_repository import OwnershipRepository
from app.schemas.case import CaseTransitionRequest
from app.services.audit_service import AuditService
from app.services.case_service import CaseService
from app.services.policy_service import PolicyService


@pytest.fixture
def case_service(db_session: Session):
    """Create a case service with all dependencies."""
    case_repo = CaseRepository(db_session)
    history_repo = HistoryRepository(db_session)
    ownership_repo = OwnershipRepository(db_session)
    config_repo = ConfigRepository(db_session)
    audit_repo = AuditRepository(db_session)
    
    policy_service = PolicyService(config_repo)
    audit_service = AuditService(audit_repo, Clock())
    customer_case_adapter = CustomerCaseAdapter()
    
    # Seed eligibility rule
    now = datetime.now(datetime.now().tzinfo)
    rule = IssueEligibilityRule(
        id=uuid.uuid4(),
        issue_type="account_query",
        is_eligible=True,
        priority_weight=100,
        created_at=now
    )
    db_session.add(rule)
    
    # Seed owner mapping
    owner_mapping = OwnerTeamMapping(
        id=uuid.uuid4(),
        owner_team_code="case_ops",
        owner_semantic_label="Operations",
        owner_display_name="Case Operations Team",
        is_active=True,
        created_at=now
    )
    db_session.add(owner_mapping)
    
    # Seed lifecycle transitions
    transitions = [
        CaseLifecycleTransition(
            id=uuid.uuid4(),
            from_state="case_created",
            to_state="under_review",
            basis_type="operational_event",
            is_active=True,
            created_at=now
        ),
        CaseLifecycleTransition(
            id=uuid.uuid4(),
            from_state="case_created",
            to_state="in_progress",
            basis_type="approved_manual_update",
            is_active=True,
            created_at=now
        ),
        CaseLifecycleTransition(
            id=uuid.uuid4(),
            from_state="under_review",
            to_state="in_progress",
            basis_type="operational_event",
            is_active=True,
            created_at=now
        ),
        CaseLifecycleTransition(
            id=uuid.uuid4(),
            from_state="in_progress",
            to_state="resolved",
            basis_type="operational_event",
            is_active=True,
            created_at=now
        ),
        CaseLifecycleTransition(
            id=uuid.uuid4(),
            from_state="resolved",
            to_state="closed",
            basis_type="approved_manual_update",
            is_active=True,
            created_at=now
        ),
    ]
    for transition in transitions:
        db_session.add(transition)
    
    db_session.commit()
    
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


@pytest.fixture
def sample_case(db_session: Session):
    """Create a sample case for testing."""
    now = datetime.now(datetime.now().tzinfo)
    case_id = uuid.uuid4()
    
    # Create case
    case = Case(
        id=case_id,
        case_reference="CP-TEST12345",
        customer_party_id="CUST-001",
        brand="lloyds",
        issue_type="account_query",
        classification_source="eligibility_rule",
        issue_title="Test Account Query",
        issue_summary="Test summary",
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
    
    # Create anchor link
    anchor_link = CaseAnchorLink(
        id=uuid.uuid4(),
        case_id=case_id,
        anchor_domain="customer_case",
        anchor_system="core",
        anchor_record_type="case",
        anchor_record_id="test-001",
        anchor_reference="ANCHOR-001",
        link_status="active",
        created_at=now
    )
    db_session.add(anchor_link)
    
    # Create status projection
    projection = CaseStatusProjection(
        id=uuid.uuid4(),
        case_id=case_id,
        status_code="received",
        status_label="Received",
        lifecycle_state="case_created",
        status_icon="in_progress",
        status_color="blue",
        customer_facing_text="Your case has been received.",
        next_step_text="We're reviewing your case.",
        effective_from=now,
        is_current=True,
        created_at=now
    )
    db_session.add(projection)
    
    # Create ownership
    ownership = CaseOwnership(
        id=uuid.uuid4(),
        case_id=case_id,
        owner_team_code="case_ops",
        owner_semantic_label="Operations",
        owner_display_name="Case Operations Team",
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
        customer_explanatory_text="We're reviewing the timing.",
        confidence_basis="initial",
        effective_from=now,
        is_current=True,
        created_at=now
    )
    db_session.add(expected_by)
    
    # Create initial event
    event = CaseEvent(
        id=uuid.uuid4(),
        case_id=case_id,
        sequence_number=1,
        event_type="CaseCaptured",
        event_timestamp=now,
        summary_text="Case created",
        customer_visible_flag=True,
        actor_type="customer",
        correlation_id=str(uuid.uuid4()),
        created_at=now
    )
    db_session.add(event)
    
    db_session.commit()
    
    return case


def test_lifecycle_graph_loads_transitions(db_session: Session, case_service):
    """Test that lifecycle graph loads transitions from database."""
    config_repo = ConfigRepository(db_session)
    graph = LifecycleGraph(config_repo)
    
    # Should allow seeded transitions
    assert graph.is_allowed("case_created", "in_progress", "approved_manual_update") is True
    assert graph.is_allowed("in_progress", "resolved", "operational_event") is True


def test_transition_case_success(db_session: Session, case_service, sample_case):
    """Test successful case transition."""
    request = CaseTransitionRequest(
        to_state="in_progress",
        basis_type="approved_manual_update",
        basis_reference="APPROVAL-001",
        status_code="in_progress",
        status_label="In Progress",
        status_summary_text="We're working on your case and will update you soon.",
        next_step_text="We'll contact you when we have more information."
    )
    
    result = case_service.transition(
        case_reference="CP-TEST12345",
        request=request,
        correlation_id=str(uuid.uuid4())
    )
    
    # Check result
    assert result.case.current_lifecycle_state == "in_progress"
    assert result.case.status_code == "in_progress"
    assert result.case.status_label == "In Progress"
    assert result.event.event_type == "CaseStatusChanged"
    assert result.event.lifecycle_from == "case_created"
    assert result.event.lifecycle_to == "in_progress"
    
    # Check database
    case = db_session.query(Case).filter_by(case_reference="CP-TEST12345").first()
    assert case.current_lifecycle_state == "in_progress"
    assert case.continuity_state == "refresh_pending"


def test_transition_invalid_transition(db_session: Session, case_service, sample_case):
    """Test that invalid transitions are rejected."""
    from app.core.errors import ValidationError
    
    request = CaseTransitionRequest(
        to_state="closed",
        basis_type="operational_event",
        basis_reference="INVALID-001",
        status_code="closed",
        status_label="Closed",
        status_summary_text="Case closed.",
        outcome_summary="Test outcome"
    )
    
    with pytest.raises(ValidationError, match="not allowed"):
        case_service.transition(
            case_reference="CP-TEST12345",
            request=request,
            correlation_id=str(uuid.uuid4())
        )


def test_transition_same_state(db_session: Session, case_service, sample_case):
    """Test that transitioning to the same state is rejected."""
    from app.core.errors import ValidationError
    
    request = CaseTransitionRequest(
        to_state="case_created",
        basis_type="operational_event",
        basis_reference="INVALID-001",
        status_code="received",
        status_label="Received",
        status_summary_text="Still received."
    )
    
    with pytest.raises(ValidationError, match="already in state"):
        case_service.transition(
            case_reference="CP-TEST12345",
            request=request,
            correlation_id=str(uuid.uuid4())
        )


def test_transition_close_without_outcome(db_session: Session, case_service, sample_case):
    """Test that closing without outcome_summary is rejected."""
    from app.core.errors import ValidationError
    
    # First transition to resolved
    request1 = CaseTransitionRequest(
        to_state="in_progress",
        basis_type="approved_manual_update",
        basis_reference="APPROVAL-001",
        status_code="in_progress",
        status_label="In Progress",
        status_summary_text="In progress."
    )
    case_service.transition(
        case_reference="CP-TEST12345",
        request=request1,
        correlation_id=str(uuid.uuid4())
    )
    db_session.commit()
    
    request2 = CaseTransitionRequest(
        to_state="resolved",
        basis_type="operational_event",
        basis_reference="RESOLVE-001",
        status_code="resolved",
        status_label="Resolved",
        status_summary_text="Resolved."
    )
    case_service.transition(
        case_reference="CP-TEST12345",
        request=request2,
        correlation_id=str(uuid.uuid4())
    )
    db_session.commit()
    
    # Try to close without outcome
    request3 = CaseTransitionRequest(
        to_state="closed",
        basis_type="approved_manual_update",
        basis_reference="CLOSE-001",
        status_code="closed",
        status_label="Closed",
        status_summary_text="Closed."
    )
    
    with pytest.raises(ValidationError, match="outcome_summary is required"):
        case_service.transition(
            case_reference="CP-TEST12345",
            request=request3,
            correlation_id=str(uuid.uuid4())
        )

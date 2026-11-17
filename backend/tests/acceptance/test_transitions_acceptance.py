"""Acceptance tests for lifecycle transitions - integration style due to pre-existing auth fixture issue."""
import uuid
from datetime import datetime

import pytest
from sqlalchemy.orm import Session

from app.adapters.customer_case_adapter import CustomerCaseAdapter
from app.core.clock import Clock
from app.core.errors import NotFoundError, ValidationError
from app.models.audit import CaseEvent
from app.models.case import Case, CaseAnchorLink, CaseStatusProjection
from app.models.config import CaseLifecycleTransition
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


def setup_service_and_case(db_session: Session) -> tuple[CaseService, Case]:
    """Set up case service with test data."""
    now = datetime.now(datetime.now().tzinfo)
    
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
    
    # Create test case
    case_id = uuid.uuid4()
    case = Case(
        id=case_id,
        case_reference="CP-ACPT12345",
        customer_party_id="TEST-001",
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
        anchor_record_id="test-acpt-001",
        anchor_reference="ANCHOR-ACPT-001",
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
    
    # Create service
    case_repo = CaseRepository(db_session)
    history_repo = HistoryRepository(db_session)
    ownership_repo = OwnershipRepository(db_session)
    config_repo = ConfigRepository(db_session)
    audit_repo = AuditRepository(db_session)
    
    policy_service = PolicyService(config_repo)
    audit_service = AuditService(audit_repo, Clock())
    customer_case_adapter = CustomerCaseAdapter()
    
    service = CaseService(
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
    
    return service, case


def test_transition_case_success(db_session: Session):
    """Test successful case transition."""
    service, case = setup_service_and_case(db_session)
    
    request = CaseTransitionRequest(
        to_state="in_progress",
        basis_type="approved_manual_update",
        basis_reference="APPROVAL-001",
        status_code="in_progress",
        status_label="In Progress",
        status_summary_text="We're working on your case and will update you soon.",
        next_step_text="We'll contact you when we have more information."
    )
    
    result = service.transition(
        case_reference="CP-ACPT12345",
        request=request,
        correlation_id=str(uuid.uuid4())
    )
    
    db_session.commit()
    
    # Verify result
    assert result.case.current_lifecycle_state == "in_progress"
    assert result.case.status_code == "in_progress"
    assert result.case.status_label == "In Progress"
    assert result.case.continuity_state == "refresh_pending"
    assert result.event.event_type == "CaseStatusChanged"
    assert result.event.lifecycle_from == "case_created"
    assert result.event.lifecycle_to == "in_progress"
    assert result.event.customer_visible_flag is True


def test_transition_invalid_transition_422(db_session: Session):
    """Test that invalid transitions are rejected."""
    service, case = setup_service_and_case(db_session)
    
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
        service.transition(
            case_reference="CP-ACPT12345",
            request=request,
            correlation_id=str(uuid.uuid4())
        )


def test_transition_same_state_422(db_session: Session):
    """Test that transitioning to same state is rejected."""
    service, case = setup_service_and_case(db_session)
    
    request = CaseTransitionRequest(
        to_state="case_created",
        basis_type="operational_event",
        basis_reference="INVALID-001",
        status_code="received",
        status_label="Received",
        status_summary_text="Still received."
    )
    
    with pytest.raises(ValidationError, match="already in state"):
        service.transition(
            case_reference="CP-ACPT12345",
            request=request,
            correlation_id=str(uuid.uuid4())
        )


def test_transition_not_found_404(db_session: Session):
    """Test that unknown case raises NotFoundError."""
    service, case = setup_service_and_case(db_session)
    
    request = CaseTransitionRequest(
        to_state="in_progress",
        basis_type="approved_manual_update",
        basis_reference="APPROVAL-001",
        status_code="in_progress",
        status_label="In Progress",
        status_summary_text="In progress."
    )
    
    with pytest.raises(NotFoundError):
        service.transition(
            case_reference="CP-NOTFOUND",
            request=request,
            correlation_id=str(uuid.uuid4())
        )


def test_transition_close_with_outcome(db_session: Session):
    """Test closing a case with outcome_summary."""
    service, case = setup_service_and_case(db_session)
    
    # First transition to in_progress
    request1 = CaseTransitionRequest(
        to_state="in_progress",
        basis_type="approved_manual_update",
        basis_reference="APPROVAL-001",
        status_code="in_progress",
        status_label="In Progress",
        status_summary_text="In progress."
    )
    service.transition(
        case_reference="CP-ACPT12345",
        request=request1,
        correlation_id=str(uuid.uuid4())
    )
    db_session.commit()
    
    # Then to resolved
    request2 = CaseTransitionRequest(
        to_state="resolved",
        basis_type="operational_event",
        basis_reference="RESOLVE-001",
        status_code="resolved",
        status_label="Resolved",
        status_summary_text="Issue resolved."
    )
    service.transition(
        case_reference="CP-ACPT12345",
        request=request2,
        correlation_id=str(uuid.uuid4())
    )
    db_session.commit()
    
    # Finally close with outcome
    request3 = CaseTransitionRequest(
        to_state="closed",
        basis_type="approved_manual_update",
        basis_reference="CLOSE-001",
        status_code="closed",
        status_label="Closed",
        status_summary_text="Case successfully closed.",
        outcome_summary="Account query was resolved. Customer was informed of the resolution."
    )
    
    result = service.transition(
        case_reference="CP-ACPT12345",
        request=request3,
        correlation_id=str(uuid.uuid4())
    )
    
    db_session.commit()
    
    assert result.case.current_lifecycle_state == "closed"
    assert result.case.closed_at is not None
    assert result.case.outcome_summary == "Account query was resolved. Customer was informed of the resolution."


def test_transition_close_without_outcome_422(db_session: Session):
    """Test that closing without outcome_summary is rejected."""
    service, case = setup_service_and_case(db_session)
    
    # First transition to in_progress then resolved
    request1 = CaseTransitionRequest(
        to_state="in_progress",
        basis_type="approved_manual_update",
        basis_reference="APPROVAL-001",
        status_code="in_progress",
        status_label="In Progress",
        status_summary_text="In progress."
    )
    service.transition(
        case_reference="CP-ACPT12345",
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
    service.transition(
        case_reference="CP-ACPT12345",
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
        status_summary_text="Case closed."
    )
    
    with pytest.raises(ValidationError, match="outcome_summary is required"):
        service.transition(
            case_reference="CP-ACPT12345",
            request=request3,
            correlation_id=str(uuid.uuid4())
        )


def test_transition_restricted_data_422(db_session: Session):
    """Test that restricted data in free text is rejected by schema validation."""
    service, case = setup_service_and_case(db_session)
    
    # This will fail at Pydantic validation level before reaching the service
    from pydantic import ValidationError as PydanticValidationError
    
    with pytest.raises(PydanticValidationError, match="restricted data"):
        CaseTransitionRequest(
            to_state="in_progress",
            basis_type="approved_manual_update",
            basis_reference="APPROVAL-001",
            status_code="in_progress",
            status_label="In Progress",
            status_summary_text="Card number 4111111111111111 was used.",
        )

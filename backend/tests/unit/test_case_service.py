"""Unit tests for case service."""
import uuid
from datetime import datetime, timezone
from unittest.mock import MagicMock, Mock

import pytest

from app.adapters.customer_case_adapter import CustomerCaseAdapter
from app.core.clock import Clock
from app.core.errors import NotFoundError
from app.models.audit import CaseEvent
from app.models.case import Case, CaseAnchorLink, CaseStatusProjection
from app.models.config import IssueEligibilityRule, OwnerTeamMapping
from app.models.ownership import CaseOwnership, ExpectedByCommitment
from app.repositories.audit_repository import AuditRepository
from app.repositories.case_repository import CaseRepository
from app.repositories.config_repository import ConfigRepository
from app.repositories.history_repository import HistoryRepository
from app.repositories.ownership_repository import OwnershipRepository
from app.schemas.case import CaseCreateRequest
from app.services.audit_service import AuditService
from app.services.case_service import CaseService
from app.services.policy_service import PolicyService, PolicyResult


@pytest.fixture
def mock_repos():
    """Create mock repositories."""
    return {
        "case_repo": MagicMock(spec=CaseRepository),
        "history_repo": MagicMock(spec=HistoryRepository),
        "ownership_repo": MagicMock(spec=OwnershipRepository),
        "config_repo": MagicMock(spec=ConfigRepository),
        "audit_repo": MagicMock(spec=AuditRepository),
    }


@pytest.fixture
def mock_services():
    """Create mock services."""
    policy_service = MagicMock(spec=PolicyService)
    audit_service = MagicMock(spec=AuditService)
    customer_case_adapter = MagicMock(spec=CustomerCaseAdapter)
    clock = MagicMock()
    clock.now = MagicMock(return_value=datetime.now(timezone.utc))
    
    return {
        "policy_service": policy_service,
        "audit_service": audit_service,
        "customer_case_adapter": customer_case_adapter,
        "clock": clock,
    }


@pytest.fixture
def case_service(mock_repos, mock_services):
    """Create case service with mocked dependencies."""
    return CaseService(
        case_repo=mock_repos["case_repo"],
        history_repo=mock_repos["history_repo"],
        ownership_repo=mock_repos["ownership_repo"],
        config_repo=mock_repos["config_repo"],
        audit_repo=mock_repos["audit_repo"],
        policy_service=mock_services["policy_service"],
        audit_service=mock_services["audit_service"],
        customer_case_adapter=mock_services["customer_case_adapter"],
        clock=mock_services["clock"],
    )


def test_create_case_surfaces_existing_open_case(case_service, mock_repos, mock_services):
    """Test that create_case surfaces an existing open case instead of creating duplicate."""
    # Setup
    request = CaseCreateRequest(
        issue_type="card_declined",
        issue_summary="My card was declined",
        origin_channel="mobile_app"
    )
    
    # Mock existing case found
    existing_case = Mock(spec=Case)
    existing_case.id = uuid.uuid4()
    existing_case.case_reference = "CP-EXISTING"
    existing_case.classification_source = "eligibility_rule"
    existing_case.continuity_state = "package_current"
    existing_case.customer_party_id = "CUST-001"
    existing_case.brand = "lloyds"
    existing_case.issue_type = "card_declined"
    existing_case.issue_title = "Card Declined"
    existing_case.issue_summary = "My card was declined"
    existing_case.origin_channel = "mobile_app"
    existing_case.current_lifecycle_state = "case_created"
    existing_case.current_status_code = "received"
    existing_case.current_status_label = "Received"
    existing_case.latest_meaningful_update_at = None
    existing_case.opened_at = datetime.now(timezone.utc)
    existing_case.closed_at = None
    existing_case.outcome_summary = None
    existing_case.continuity_state = "package_current"
    
    mock_repos["case_repo"].find_open_by_issue_type.return_value = existing_case
    
    # Mock projections
    projection = Mock(spec=CaseStatusProjection)
    projection.status_code = "received"
    projection.status_label = "Received"
    projection.customer_facing_text = "Your case has been received"
    projection.next_step_text = "We're reviewing your case"
    
    owner = Mock(spec=CaseOwnership)
    owner.owner_team_code = "INTAKE_DEFAULT"
    owner.owner_semantic_label = "Intake Team"
    owner.owner_display_name = "Intake & Triage"
    owner.effective_from = datetime.now(timezone.utc)
    
    expected_by = Mock(spec=ExpectedByCommitment)
    expected_by.commitment_state = "under_review"
    expected_by.expected_by_at = None
    expected_by.customer_explanatory_text = "Under review"
    expected_by.confidence_basis = "initial"
    expected_by.effective_from = datetime.now(timezone.utc)
    
    mock_repos["case_repo"].current_projection.return_value = projection
    mock_repos["ownership_repo"].current_ownership.return_value = owner
    mock_repos["ownership_repo"].current_expected_by.return_value = expected_by
    
    # Execute
    result = case_service.create_case(
        principal_customer_party_id="CUST-001",
        principal_brand="lloyds",
        request=request,
        correlation_id="test-corr-001"
    )
    
    # Assert
    assert result.outcome == "surfaced"
    assert result.case is not None
    assert result.case.case_reference == "CP-EXISTING"
    assert result.classification_source == "eligibility_rule"
    assert result.continuity_available is True
    
    # Verify no case was created
    mock_repos["case_repo"].create.assert_not_called()


def test_create_case_returns_not_eligible_when_policy_denies(case_service, mock_repos, mock_services):
    """Test that create_case returns not_eligible when policy decision denies."""
    # Setup
    request = CaseCreateRequest(
        issue_type="general_query",
        issue_summary="General question",
        origin_channel="mobile_app"
    )
    
    # No existing case
    mock_repos["case_repo"].find_open_by_issue_type.return_value = None
    
    # Policy denies
    mock_services["policy_service"].decide.return_value = PolicyResult(
        outcome="deny",
        denial_reason_code="issue_type_not_eligible"
    )
    
    # Mock config rule
    rule = Mock(spec=IssueEligibilityRule)
    rule.redirect_journey_code = "existing_support"
    mock_repos["config_repo"].active_rule.return_value = rule
    
    # Execute
    result = case_service.create_case(
        principal_customer_party_id="CUST-001",
        principal_brand="lloyds",
        request=request,
        correlation_id="test-corr-002"
    )
    
    # Assert
    assert result.outcome == "not_eligible"
    assert result.case is None
    assert result.redirect_journey_code == "existing_support"
    assert result.redirect_message is not None
    
    # Verify no case was created
    mock_repos["case_repo"].create.assert_not_called()
    mock_services["customer_case_adapter"].create_case.assert_not_called()


def test_create_case_creates_new_case_successfully(case_service, mock_repos, mock_services):
    """Test successful case creation."""
    # Setup
    request = CaseCreateRequest(
        issue_type="card_declined",
        issue_summary="My card was declined at store",
        origin_channel="mobile_app"
    )
    
    # No existing case
    mock_repos["case_repo"].find_open_by_issue_type.return_value = None
    
    # Policy allows
    mock_services["policy_service"].decide.return_value = PolicyResult(outcome="allow")
    
    # Adapter returns anchor
    mock_services["customer_case_adapter"].create_case.return_value = {
        "anchor_domain": "customer_case",
        "anchor_system": "case_management",
        "anchor_record_type": "case",
        "anchor_record_id": "MOCK-123",
        "anchor_reference": "CC-MOCK-123"
    }
    
    # Mock owner mapping
    owner_mapping = Mock(spec=OwnerTeamMapping)
    owner_mapping.owner_team_code = "INTAKE_DEFAULT"
    owner_mapping.owner_semantic_label = "Intake Team"
    owner_mapping.owner_display_name = "Intake & Triage"
    mock_repos["ownership_repo"].active_mapping.return_value = owner_mapping
    
    # Mock sequence number
    mock_repos["history_repo"].next_sequence.return_value = 1
    
    # Mock current projections for response
    mock_repos["case_repo"].current_projection.return_value = Mock(
        status_code="received",
        status_label="Received",
        customer_facing_text="Your case has been received",
        next_step_text="We're reviewing your case"
    )
    mock_repos["ownership_repo"].current_ownership.return_value = Mock(
        owner_team_code="INTAKE_DEFAULT",
        owner_semantic_label="Intake Team",
        owner_display_name="Intake & Triage",
        effective_from=datetime.now(timezone.utc)
    )
    mock_repos["ownership_repo"].current_expected_by.return_value = Mock(
        commitment_state="under_review",
        expected_by_at=None,
        customer_explanatory_text="Under review",
        confidence_basis="initial",
        effective_from=datetime.now(timezone.utc)
    )
    
    # Execute
    result = case_service.create_case(
        principal_customer_party_id="CUST-001",
        principal_brand="lloyds",
        request=request,
        correlation_id="test-corr-003"
    )
    
    # Assert
    assert result.outcome == "created"
    assert result.case is not None
    assert result.case.case_reference.startswith("CP-")
    assert result.classification_source == "eligibility_rule"
    assert result.anchor_reference == "CC-MOCK-123"
    assert result.continuity_available is False
    
    # Verify all components were created
    mock_repos["case_repo"].create.assert_called_once()
    mock_repos["case_repo"].create_anchor_link.assert_called_once()
    mock_repos["case_repo"].create_status_projection.assert_called_once()
    mock_repos["ownership_repo"].insert_ownership.assert_called_once()
    mock_repos["ownership_repo"].insert_expected_by.assert_called_once()
    mock_repos["history_repo"].add_event.assert_called_once()
    mock_services["audit_service"].record.assert_called_once()


def test_get_case_raises_not_found_when_case_missing(case_service, mock_repos):
    """Test that get_case raises NotFound when case doesn't exist."""
    # Setup
    mock_repos["case_repo"].get_by_reference_for_customer.return_value = None
    
    # Execute and assert
    with pytest.raises(NotFoundError):
        case_service.get_case(
            customer_party_id="CUST-001",
            case_reference="CP-NONEXISTENT"
        )


def test_get_case_returns_case_detail(case_service, mock_repos):
    """Test successful case retrieval."""
    # Setup
    case = Mock(spec=Case)
    case.id = uuid.uuid4()
    case.case_reference = "CP-TEST123"
    case.customer_party_id = "CUST-001"
    case.brand = "lloyds"
    case.issue_type = "card_declined"
    case.classification_source = "eligibility_rule"
    case.issue_title = "Card Declined"
    case.issue_summary = "My card was declined"
    case.origin_channel = "mobile_app"
    case.current_lifecycle_state = "case_created"
    case.current_status_code = "received"
    case.current_status_label = "Received"
    case.latest_meaningful_update_at = None
    case.opened_at = datetime.now(timezone.utc)
    case.closed_at = None
    case.outcome_summary = None
    case.continuity_state = "none"
    
    projection = Mock(spec=CaseStatusProjection)
    projection.status_code = "received"
    projection.status_label = "Received"
    projection.customer_facing_text = "Your case has been received"
    projection.next_step_text = "We're reviewing your case"
    
    owner = Mock(spec=CaseOwnership)
    owner.owner_team_code = "INTAKE_DEFAULT"
    owner.owner_semantic_label = "Intake Team"
    owner.owner_display_name = "Intake & Triage"
    owner.effective_from = datetime.now(timezone.utc)
    
    expected_by = Mock(spec=ExpectedByCommitment)
    expected_by.commitment_state = "under_review"
    expected_by.expected_by_at = None
    expected_by.customer_explanatory_text = "Under review"
    expected_by.confidence_basis = "initial"
    expected_by.effective_from = datetime.now(timezone.utc)
    
    mock_repos["case_repo"].get_by_reference_for_customer.return_value = case
    mock_repos["case_repo"].current_projection.return_value = projection
    mock_repos["ownership_repo"].current_ownership.return_value = owner
    mock_repos["ownership_repo"].current_expected_by.return_value = expected_by
    
    # Execute
    result = case_service.get_case(
        customer_party_id="CUST-001",
        case_reference="CP-TEST123"
    )
    
    # Assert
    assert result.case_reference == "CP-TEST123"
    assert result.customer_party_id == "CUST-001"
    assert result.issue_type == "card_declined"

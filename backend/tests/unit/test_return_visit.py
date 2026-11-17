"""Unit tests for return visit functionality."""
import uuid
from datetime import datetime, timezone
from unittest.mock import MagicMock

import pytest

from app.core.clock import Clock
from app.core.errors import NotFoundError
from app.services.continuity_service import ContinuityService


@pytest.fixture
def mock_repos():
    """Mock repositories."""
    return {
        "continuity_repo": MagicMock(),
        "case_repo": MagicMock(),
        "ownership_repo": MagicMock(),
        "history_repo": MagicMock(),
        "audit_repo": MagicMock(),
    }


@pytest.fixture
def mock_audit_service():
    """Mock audit service."""
    return MagicMock()


@pytest.fixture
def continuity_service(mock_repos, mock_audit_service):
    """Create continuity service with mocked dependencies."""
    return ContinuityService(
        continuity_repo=mock_repos["continuity_repo"],
        case_repo=mock_repos["case_repo"],
        ownership_repo=mock_repos["ownership_repo"],
        history_repo=mock_repos["history_repo"],
        audit_repo=mock_repos["audit_repo"],
        audit_service=mock_audit_service,
        clock=Clock()
    )


def test_restore_return_visit_success(continuity_service, mock_repos):
    """Test successful return visit restoration."""
    # Arrange
    case_reference = "CP-TEST1"
    return_session_token = "valid-token-123"
    customer_party_id = "CUST-002"
    
    # Mock case
    mock_case = MagicMock()
    mock_case.id = uuid.UUID(int=1001)
    mock_case.case_reference = case_reference
    mock_case.customer_party_id = customer_party_id
    mock_case.brand = "lloyds"
    mock_case.issue_type = "card_declined"
    mock_case.classification_source = "eligibility_rule"
    mock_case.issue_title = "Card Declined"
    mock_case.issue_summary = "My card was declined"
    mock_case.origin_channel = "mobile_app"
    mock_case.current_lifecycle_state = "under_review"
    mock_case.current_status_code = "reviewing"
    mock_case.current_status_label = "Under Review"
    mock_case.latest_meaningful_update_text = "Case under review"
    mock_case.latest_meaningful_update_at = datetime.now(timezone.utc)
    mock_case.opened_at = datetime.now(timezone.utc)
    mock_case.closed_at = None
    mock_case.outcome_summary = None
    mock_case.continuity_state = "package_current"
    
    mock_repos["case_repo"].get_by_reference_for_customer.return_value = mock_case
    
    # Mock context
    mock_context = MagicMock()
    mock_context.package_version = 5
    mock_repos["continuity_repo"].current_package.return_value = mock_context
    
    # Mock events
    mock_event = MagicMock()
    mock_event.event_type = "CaseStatusChanged"
    mock_event.summary_text = "Case status updated"
    mock_event.event_timestamp = datetime.now(timezone.utc)
    mock_event.customer_visible_flag = True
    
    mock_repos["history_repo"].page_for_case.return_value = ([mock_event], 1)
    
    # Mock ownership
    mock_owner = MagicMock()
    mock_owner.owner_team_code = "CARDS_DISPUTES"
    mock_owner.owner_semantic_label = "Card Disputes Team"
    mock_owner.owner_display_name = "Card Disputes"
    mock_owner.effective_from = datetime.now(timezone.utc)
    mock_repos["ownership_repo"].current_ownership.return_value = mock_owner
    
    # Mock expected by
    mock_expected_by = MagicMock()
    mock_expected_by.expected_by_at = datetime.now(timezone.utc)
    mock_expected_by.customer_explanatory_text = "We'll update you soon"
    mock_expected_by.commitment_state = "under_review"
    mock_expected_by.effective_from = datetime.now(timezone.utc)
    mock_repos["ownership_repo"].current_expected_by.return_value = mock_expected_by
    
    # Act
    result = continuity_service.restore_return_visit(
        case_reference=case_reference,
        return_session_token=return_session_token,
        channel="mobile_app",
        correlation_id="test-correlation-123"
    )
    
    # Assert
    assert "case" in result
    assert "recent_updates" in result
    assert "context_version" in result
    assert "return_visit_restored_at" in result
    assert result["context_version"] == 5
    assert len(result["recent_updates"]) == 1
    assert result["recent_updates"][0]["event_type"] == "CaseStatusChanged"
    
    # Verify case was retrieved with customer scoping
    mock_repos["case_repo"].get_by_reference_for_customer.assert_called_once_with(
        case_reference, customer_party_id
    )
    
    # Verify history was retrieved with customer-visible only
    mock_repos["history_repo"].page_for_case.assert_called_once_with(
        mock_case.id, limit=10, offset=0, customer_visible_only=True
    )


def test_restore_return_visit_case_not_found(continuity_service, mock_repos):
    """Test return visit restoration when case not found."""
    # Arrange
    case_reference = "CP-NOTFOUND"
    return_session_token = "valid-token-123"
    
    mock_repos["case_repo"].get_by_reference_for_customer.return_value = None
    
    # Act & Assert
    with pytest.raises(NotFoundError, match="Case CP-NOTFOUND not found"):
        continuity_service.restore_return_visit(
            case_reference=case_reference,
            return_session_token=return_session_token
        )


def test_restore_return_visit_invalid_token(continuity_service):
    """Test return visit restoration with invalid token."""
    # Arrange
    case_reference = "CP-TEST1"
    return_session_token = ""  # Invalid empty token
    
    # Act & Assert
    with pytest.raises(ValueError, match="Invalid return session token"):
        continuity_service.restore_return_visit(
            case_reference=case_reference,
            return_session_token=return_session_token
        )


def test_restore_return_visit_no_context_version_defaults_to_one(continuity_service, mock_repos):
    """Test return visit restoration when no context exists yet."""
    # Arrange
    case_reference = "CP-TEST1"
    return_session_token = "valid-token-123"
    customer_party_id = "CUST-002"
    
    # Mock case
    mock_case = MagicMock()
    mock_case.id = uuid.UUID(int=1001)
    mock_case.case_reference = case_reference
    mock_case.customer_party_id = customer_party_id
    mock_case.brand = "bank_of_scotland"
    mock_case.issue_type = "payment_missing"
    mock_case.classification_source = "eligibility_rule"
    mock_case.issue_title = "Payment Missing"
    mock_case.issue_summary = "My payment is missing"
    mock_case.origin_channel = "ai_assistant"
    mock_case.current_lifecycle_state = "captured"
    mock_case.current_status_code = "received"
    mock_case.current_status_label = "Received"
    mock_case.latest_meaningful_update_text = None
    mock_case.latest_meaningful_update_at = None
    mock_case.opened_at = datetime.now(timezone.utc)
    mock_case.closed_at = None
    mock_case.outcome_summary = None
    mock_case.continuity_state = "none"
    
    mock_repos["case_repo"].get_by_reference_for_customer.return_value = mock_case
    
    # Mock no existing context
    mock_repos["continuity_repo"].current_package.return_value = None
    
    # Mock empty events
    mock_repos["history_repo"].page_for_case.return_value = ([], 0)
    
    # Mock ownership
    mock_owner = MagicMock()
    mock_owner.owner_team_code = "INTAKE_DEFAULT"
    mock_owner.owner_semantic_label = "Intake Team"
    mock_owner.owner_display_name = "Intake & Triage"
    mock_owner.effective_from = datetime.now(timezone.utc)
    mock_repos["ownership_repo"].current_ownership.return_value = mock_owner
    
    # Mock expected by
    mock_expected_by = MagicMock()
    mock_expected_by.expected_by_at = None
    mock_expected_by.customer_explanatory_text = "We're reviewing the timing"
    mock_expected_by.commitment_state = "under_review"
    mock_expected_by.effective_from = datetime.now(timezone.utc)
    mock_repos["ownership_repo"].current_expected_by.return_value = mock_expected_by
    
    # Act
    result = continuity_service.restore_return_visit(
        case_reference=case_reference,
        return_session_token=return_session_token,
        channel="ai_assistant"
    )
    
    # Assert
    assert result["context_version"] == 1  # Defaults to 1 when no context exists
    assert result["recent_updates"] == []


def test_restore_return_visit_audit_called_with_correlation_id(continuity_service, mock_repos, mock_audit_service):
    """Test return visit restoration records audit entry."""
    # Arrange
    case_reference = "CP-TEST1"
    return_session_token = "valid-token-123"
    correlation_id = "correlation-audit-123"
    customer_party_id = "CUST-002"
    
    # Mock case
    mock_case = MagicMock()
    mock_case.id = uuid.UUID(int=1001)
    mock_case.case_reference = case_reference
    mock_case.customer_party_id = customer_party_id
    mock_case.brand = "lloyds"
    mock_case.issue_type = "card_declined"
    mock_case.classification_source = "eligibility_rule"
    mock_case.issue_title = "Card Declined"
    mock_case.issue_summary = "Test"
    mock_case.origin_channel = "mobile_app"
    mock_case.current_lifecycle_state = "captured"
    mock_case.current_status_code = "received"
    mock_case.current_status_label = "Received"
    mock_case.latest_meaningful_update_text = None
    mock_case.latest_meaningful_update_at = None
    mock_case.opened_at = datetime.now(timezone.utc)
    mock_case.closed_at = None
    mock_case.outcome_summary = None
    mock_case.continuity_state = "none"
    
    mock_repos["case_repo"].get_by_reference_for_customer.return_value = mock_case
    mock_repos["continuity_repo"].current_package.return_value = None
    mock_repos["history_repo"].page_for_case.return_value = ([], 0)
    
    mock_owner = MagicMock()
    mock_owner.owner_team_code = "INTAKE_DEFAULT"
    mock_owner.owner_semantic_label = "Intake Team"
    mock_owner.owner_display_name = "Intake"
    mock_owner.effective_from = datetime.now(timezone.utc)
    mock_repos["ownership_repo"].current_ownership.return_value = mock_owner
    
    mock_expected_by = MagicMock()
    mock_expected_by.expected_by_at = None
    mock_expected_by.customer_explanatory_text = "Test"
    mock_expected_by.commitment_state = "under_review"
    mock_expected_by.effective_from = datetime.now(timezone.utc)
    mock_repos["ownership_repo"].current_expected_by.return_value = mock_expected_by
    
    # Act
    continuity_service.restore_return_visit(
        case_reference=case_reference,
        return_session_token=return_session_token,
        channel="mobile_app",
        correlation_id=correlation_id
    )
    
    # Assert
    mock_audit_service.record.assert_called_once()
    call_args = mock_audit_service.record.call_args
    assert call_args[1]["correlation_id"] == correlation_id
    assert call_args[1]["audit_category"] == "access"
    assert call_args[1]["event_type"] == "return_visit_restored"
    assert call_args[1]["actor_type"] == "customer"
    assert call_args[1]["actor_reference"] == customer_party_id
    assert call_args[1]["entity_type"] == "case"
    assert call_args[1]["entity_id"] == str(mock_case.id)

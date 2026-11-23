"""
Unit tests for PayeeService
Requirement: FR-PAY-001
"""
import uuid
from datetime import UTC, datetime
from unittest.mock import Mock

import pytest

from app.models.capability_status_record import CapabilityStatusRecord
from app.models.payee import Payee
from app.services.payee_service import PayeeService


@pytest.fixture
def mock_payee_repo():
    return Mock()


@pytest.fixture
def mock_capability_repo():
    return Mock()


@pytest.fixture
def mock_entitlement_adapter():
    return Mock()


@pytest.fixture
def payee_service(mock_payee_repo, mock_capability_repo, mock_entitlement_adapter):
    return PayeeService(mock_payee_repo, mock_capability_repo, mock_entitlement_adapter)


@pytest.fixture
def sample_customer_id():
    return uuid.UUID("00000000-0000-0000-0000-000000000001")


@pytest.fixture
def sample_payees():
    customer_id = uuid.UUID("00000000-0000-0000-0000-000000000001")
    return [
        Payee(
            id=uuid.uuid4(),
            customer_profile_ref_id=customer_id,
            payee_name="Jamie Clarke",
            payee_account_identifier="12345678",
            payee_sort_code="04-00-04",
            masked_account_identifier="****3321",
            payee_status="saved_active",
            activated_at=datetime.now(UTC),
            cop_outcome_category="match",
            cop_provider_reference="cop-ref-jamie-clarke",
            cop_checked_at=datetime.now(UTC),
            correlation_id="test-correlation-id"
        ),
        Payee(
            id=uuid.uuid4(),
            customer_profile_ref_id=customer_id,
            payee_name="Priya Patel",
            payee_account_identifier="87654321",
            payee_sort_code="60-83-71",
            masked_account_identifier="****7745",
            payee_status="saved_active",
            activated_at=datetime.now(UTC),
            cop_outcome_category="match",
            cop_provider_reference="cop-ref-priya-patel",
            cop_checked_at=datetime.now(UTC),
            correlation_id="test-correlation-id"
        ),
    ]


@pytest.fixture
def healthy_capability():
    return CapabilityStatusRecord(
        id=uuid.uuid4(),
        capability_name="saved_payees",
        status_value="healthy",
        cause_category="unknown",
        customer_message_code=None,
        recovery_guidance_code=None,
        effective_from=datetime.now(UTC)
    )


@pytest.fixture
def unavailable_capability():
    return CapabilityStatusRecord(
        id=uuid.uuid4(),
        capability_name="saved_payees",
        status_value="unavailable",
        cause_category="dependency_outage",
        customer_message_code="saved_payees_unavailable",
        recovery_guidance_code="try_again_later",
        effective_from=datetime.now(UTC)
    )


def test_get_saved_payees_success(
    payee_service,
    mock_payee_repo,
    mock_capability_repo,
    mock_entitlement_adapter,
    sample_customer_id,
    sample_payees,
    healthy_capability
):
    """Test successful retrieval of saved payees."""
    # Arrange
    mock_entitlement_adapter.check_resource_access.return_value = "allow"
    mock_capability_repo.get_current_status.return_value = healthy_capability
    mock_payee_repo.get_saved_active_payees_for_customer.return_value = (sample_payees, 2)
    
    # Act
    result = payee_service.get_saved_payees_for_customer(sample_customer_id, page=1, page_size=20)
    
    # Assert
    assert len(result.items) == 2
    assert result.total == 2
    assert result.page == 1
    assert result.page_size == 20
    assert result.capability.capability_name == "saved_payees"
    assert result.capability.status_value == "healthy"
    assert result.items[0].payee_name == "Jamie Clarke"
    assert result.items[0].payee_sort_code == "04-00-04"
    assert result.items[0].masked_account_identifier == "****3321"
    assert result.items[1].payee_name == "Priya Patel"
    
    # Verify interactions
    mock_entitlement_adapter.check_resource_access.assert_called_once_with(
        customer_id=sample_customer_id,
        resource_type="payee",
        resource_reference="*"
    )
    mock_capability_repo.get_current_status.assert_called_once_with("saved_payees")
    mock_payee_repo.get_saved_active_payees_for_customer.assert_called_once_with(
        customer_profile_ref_id=sample_customer_id,
        page=1,
        page_size=20
    )


def test_get_saved_payees_entitlement_denied(
    payee_service,
    mock_payee_repo,
    mock_capability_repo,
    mock_entitlement_adapter,
    sample_customer_id,
    healthy_capability
):
    """Test that entitlement denial returns empty page."""
    # Arrange
    mock_entitlement_adapter.check_resource_access.return_value = "deny"
    mock_capability_repo.get_current_status.return_value = healthy_capability
    
    # Act
    result = payee_service.get_saved_payees_for_customer(sample_customer_id)
    
    # Assert
    assert len(result.items) == 0
    assert result.total == 0
    assert result.capability.capability_name == "saved_payees"
    
    # Verify payee repo was not called
    mock_payee_repo.get_saved_active_payees_for_customer.assert_not_called()


def test_get_saved_payees_capability_unavailable(
    payee_service,
    mock_payee_repo,
    mock_capability_repo,
    mock_entitlement_adapter,
    sample_customer_id,
    unavailable_capability
):
    """Test that unavailable capability returns empty page with message."""
    # Arrange
    mock_entitlement_adapter.check_resource_access.return_value = "allow"
    mock_capability_repo.get_current_status.return_value = unavailable_capability
    
    # Act
    result = payee_service.get_saved_payees_for_customer(sample_customer_id)
    
    # Assert
    assert len(result.items) == 0
    assert result.total == 0
    assert result.capability.status_value == "unavailable"
    assert "unavailable" in result.capability.customer_message.lower()
    
    # Verify payee repo was not called
    mock_payee_repo.get_saved_active_payees_for_customer.assert_not_called()


def test_get_saved_payees_pagination(
    payee_service,
    mock_payee_repo,
    mock_capability_repo,
    mock_entitlement_adapter,
    sample_customer_id,
    sample_payees,
    healthy_capability
):
    """Test pagination parameters are passed correctly."""
    # Arrange
    mock_entitlement_adapter.check_resource_access.return_value = "allow"
    mock_capability_repo.get_current_status.return_value = healthy_capability
    mock_payee_repo.get_saved_active_payees_for_customer.return_value = (sample_payees[:1], 10)
    
    # Act
    result = payee_service.get_saved_payees_for_customer(sample_customer_id, page=2, page_size=1)
    
    # Assert
    assert len(result.items) == 1
    assert result.total == 10
    assert result.page == 2
    assert result.page_size == 1
    
    # Verify pagination params passed to repo
    mock_payee_repo.get_saved_active_payees_for_customer.assert_called_once_with(
        customer_profile_ref_id=sample_customer_id,
        page=2,
        page_size=1
    )


def test_get_saved_payees_empty_list(
    payee_service,
    mock_payee_repo,
    mock_capability_repo,
    mock_entitlement_adapter,
    sample_customer_id,
    healthy_capability
):
    """Test customer with no saved payees returns empty list."""
    # Arrange
    mock_entitlement_adapter.check_resource_access.return_value = "allow"
    mock_capability_repo.get_current_status.return_value = healthy_capability
    mock_payee_repo.get_saved_active_payees_for_customer.return_value = ([], 0)
    
    # Act
    result = payee_service.get_saved_payees_for_customer(sample_customer_id)
    
    # Assert
    assert len(result.items) == 0
    assert result.total == 0
    assert result.capability.status_value == "healthy"


def test_get_saved_payees_no_capability_record(
    payee_service,
    mock_payee_repo,
    mock_capability_repo,
    mock_entitlement_adapter,
    sample_customer_id,
    sample_payees
):
    """Test behavior when no capability record exists."""
    # Arrange
    mock_entitlement_adapter.check_resource_access.return_value = "allow"
    mock_capability_repo.get_current_status.return_value = None
    mock_payee_repo.get_saved_active_payees_for_customer.return_value = (sample_payees, 2)
    
    # Act
    result = payee_service.get_saved_payees_for_customer(sample_customer_id)
    
    # Assert
    assert len(result.items) == 2
    assert result.capability.status_value == "unknown"
    assert "unknown" in result.capability.customer_message.lower()

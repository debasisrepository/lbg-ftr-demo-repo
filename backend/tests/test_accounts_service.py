"""
Unit tests for account service.
Requirement: FR-ACCT-001, FR-ACCT-002, FR-ACCT-003
"""
import uuid
from datetime import UTC, datetime, timedelta
from unittest.mock import Mock

import pytest

from app.models.account_read_model import AccountReadModel
from app.models.capability_status_record import CapabilityStatusRecord
from app.services.account_service import AccountService


def test_get_accounts_overview_success(db_session):
    """Test successful account overview with current balances."""
    customer_id = uuid.UUID("00000000-0000-0000-0000-000000000001")
    
    # Mock read model service
    read_model_service = Mock()
    mock_account = AccountReadModel(
        id=uuid.uuid4(),
        customer_profile_ref_id=customer_id,
        account_system_reference="ACC-TEST-001",
        account_type="current",
        display_name="Test Account",
        masked_account_identifier="****1234",
        balance_amount_minor=100000,
        balance_currency="GBP",
        balance_availability_state="current",
        as_of_timestamp=datetime.now(UTC) - timedelta(seconds=30),
        freshness_status="within_target",
        freshness_breach_indicator=False,
        source_system_type="core_banking",
        provenance_reference="test-prov",
        projection_updated_at=datetime.now(UTC)
    )
    read_model_service.get_accounts_for_customer.return_value = ([mock_account], 1)
    
    # Mock capability service
    capability_service = Mock()
    mock_capability = CapabilityStatusRecord(
        id=uuid.uuid4(),
        capability_name="accounts_overview",
        status_value="healthy",
        cause_category="unknown",
        effective_from=datetime.now(UTC)
    )
    capability_service.get_capability_status.return_value = mock_capability
    
    # Mock entitlement adapter
    entitlement_adapter = Mock()
    entitlement_adapter.check_resource_access.return_value = "allow"
    
    # Create service
    service = AccountService(
        db=db_session,
        read_model_service=read_model_service,
        capability_service=capability_service,
        entitlement_adapter=entitlement_adapter
    )
    
    # Execute
    result = service.get_accounts_overview(customer_id, page=1, page_size=20)
    
    # Verify
    assert result.total == 1
    assert len(result.items) == 1
    assert result.items[0].account_type == "current"
    assert result.items[0].balance.amount_minor == 100000
    assert result.items[0].balance.availability_state == "current"
    assert result.items[0].freshness_status == "within_target"
    assert result.items[0].payment_source_eligible is True
    assert result.overview_state == "complete"
    assert result.capability.status_value == "healthy"
    entitlement_adapter.check_resource_access.assert_called_once()


def test_get_accounts_overview_unavailable_balance(db_session):
    """Test account with unavailable balance shows NULL amount."""
    customer_id = uuid.UUID("00000000-0000-0000-0000-000000000001")
    
    read_model_service = Mock()
    mock_account = AccountReadModel(
        id=uuid.uuid4(),
        customer_profile_ref_id=customer_id,
        account_system_reference="ACC-TEST-001",
        account_type="current",
        display_name="Test Account",
        masked_account_identifier="****1234",
        balance_amount_minor=None,  # NULL for unavailable
        balance_currency=None,
        balance_availability_state="unavailable",
        as_of_timestamp=None,
        freshness_status="unknown",
        freshness_breach_indicator=False,
        source_system_type="core_banking",
        provenance_reference="test-prov",
        projection_updated_at=datetime.now(UTC)
    )
    read_model_service.get_accounts_for_customer.return_value = ([mock_account], 1)
    
    capability_service = Mock()
    mock_capability = CapabilityStatusRecord(
        id=uuid.uuid4(),
        capability_name="accounts_overview",
        status_value="healthy",
        cause_category="unknown",
        effective_from=datetime.now(UTC)
    )
    capability_service.get_capability_status.return_value = mock_capability
    
    entitlement_adapter = Mock()
    entitlement_adapter.check_resource_access.return_value = "allow"
    
    service = AccountService(
        db=db_session,
        read_model_service=read_model_service,
        capability_service=capability_service,
        entitlement_adapter=entitlement_adapter
    )
    
    result = service.get_accounts_overview(customer_id, page=1, page_size=20)
    
    # Verify unavailable handling
    assert result.items[0].balance.amount_minor is None
    assert result.items[0].balance.currency is None
    assert result.items[0].balance.availability_state == "unavailable"
    assert result.items[0].balance.display_text == "Balance unavailable"
    assert result.items[0].item_state == "partial"
    assert result.items[0].payment_source_eligible is False
    assert result.overview_state == "partial"


def test_get_accounts_overview_stale_balance(db_session):
    """Test account with stale balance shows freshness indicator."""
    customer_id = uuid.UUID("00000000-0000-0000-0000-000000000001")
    
    read_model_service = Mock()
    stale_time = datetime.now(UTC) - timedelta(hours=2)
    mock_account = AccountReadModel(
        id=uuid.uuid4(),
        customer_profile_ref_id=customer_id,
        account_system_reference="ACC-TEST-001",
        account_type="current",
        display_name="Test Account",
        masked_account_identifier="****1234",
        balance_amount_minor=100000,
        balance_currency="GBP",
        balance_availability_state="stale",
        as_of_timestamp=stale_time,
        freshness_status="breached",
        freshness_breach_indicator=True,
        source_system_type="core_banking",
        provenance_reference="test-prov",
        projection_updated_at=stale_time
    )
    read_model_service.get_accounts_for_customer.return_value = ([mock_account], 1)
    
    capability_service = Mock()
    mock_capability = CapabilityStatusRecord(
        id=uuid.uuid4(),
        capability_name="accounts_overview",
        status_value="healthy",
        cause_category="unknown",
        effective_from=datetime.now(UTC)
    )
    capability_service.get_capability_status.return_value = mock_capability
    
    entitlement_adapter = Mock()
    entitlement_adapter.check_resource_access.return_value = "allow"
    
    service = AccountService(
        db=db_session,
        read_model_service=read_model_service,
        capability_service=capability_service,
        entitlement_adapter=entitlement_adapter
    )
    
    result = service.get_accounts_overview(customer_id, page=1, page_size=20)
    
    # Verify stale handling
    assert result.items[0].balance.amount_minor == 100000
    assert result.items[0].balance.availability_state == "stale"
    assert "(may be out of date)" in result.items[0].balance.display_text
    assert result.items[0].freshness_status == "breached"
    assert "out of date" in result.items[0].freshness_text.lower()
    assert result.items[0].payment_source_eligible is False


def test_get_accounts_overview_entitlement_denied(db_session):
    """Test entitlement denial returns 403."""
    from fastapi import HTTPException
    
    customer_id = uuid.UUID("00000000-0000-0000-0000-000000000001")
    
    entitlement_adapter = Mock()
    entitlement_adapter.check_resource_access.return_value = "deny"
    
    service = AccountService(
        db=db_session,
        entitlement_adapter=entitlement_adapter
    )
    
    with pytest.raises(HTTPException) as exc_info:
        service.get_accounts_overview(customer_id, page=1, page_size=20)
    
    assert exc_info.value.status_code == 403
    assert "entitled" in exc_info.value.detail.lower()


def test_compute_freshness_text(db_session):
    """Test freshness text computation."""
    service = AccountService(db=db_session)
    
    # Unknown
    text = service._compute_freshness_text("unknown", None)
    assert "cannot be established" in text.lower()
    
    # Breached
    text = service._compute_freshness_text("breached", datetime.now(UTC) - timedelta(hours=3))
    assert "out of date" in text.lower()
    
    # Recent (within_target)
    text = service._compute_freshness_text("within_target", datetime.now(UTC) - timedelta(seconds=30))
    assert "moments ago" in text.lower()
    
    # Minutes ago
    text = service._compute_freshness_text("within_target", datetime.now(UTC) - timedelta(minutes=5))
    assert "minute" in text.lower()
    
    # Hours ago
    text = service._compute_freshness_text("within_target", datetime.now(UTC) - timedelta(hours=2))
    assert "hour" in text.lower()


def test_format_currency(db_session):
    """Test currency formatting."""
    service = AccountService(db=db_session)
    
    # GBP formatting
    assert service._format_currency(100000, "GBP") == "£1,000.00"
    assert service._format_currency(124836, "GBP") == "£1,248.36"
    assert service._format_currency(50, "GBP") == "£0.50"
    
    # Other currency
    assert service._format_currency(100000, "USD") == "1,000.00 USD"

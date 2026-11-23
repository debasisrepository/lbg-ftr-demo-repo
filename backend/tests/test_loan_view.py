"""
Unit tests for loan view feature.
Requirement: BR-ACCT-004, BR-ACCT-007 (Release 2)
Test Cases: TC-ACCT-003 to TC-ACCT-008
"""
import uuid
from datetime import UTC, datetime, timedelta
from unittest.mock import Mock

import pytest

from app.models.account_read_model import AccountReadModel
from app.models.capability_status_record import CapabilityStatusRecord
from app.services.account_service import AccountService


def test_get_accounts_overview_with_loan_success(db_session):
    """Test loan account display with all details available (TC-ACCT-003)."""
    customer_id = uuid.UUID("00000000-0000-0000-0000-000000000003")
    
    # Mock read model service with loan data
    read_model_service = Mock()
    mock_loan = AccountReadModel(
        id=uuid.uuid4(),
        customer_profile_ref_id=customer_id,
        account_system_reference="LOAN-TEST-001",
        account_type="loan",
        display_name="Personal Loan",
        masked_account_identifier="****3456",
        balance_amount_minor=1500000,
        balance_currency="GBP",
        balance_availability_state="current",
        as_of_timestamp=datetime.now(UTC) - timedelta(seconds=30),
        freshness_status="within_target",
        freshness_breach_indicator=False,
        source_system_type="loan_servicing",
        provenance_reference="test-loan-prov",
        projection_updated_at=datetime.now(UTC),
        # Loan-specific fields
        loan_outstanding_balance_minor=1500000,
        loan_next_repayment_date=datetime.now(UTC) + timedelta(days=15),
        loan_next_repayment_amount_minor=50000,
        loan_remaining_term_months=30
    )
    read_model_service.get_accounts_for_customer.return_value = ([mock_loan], 1)
    
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
    loan_item = result.items[0]
    assert loan_item.account_type == "loan"
    assert loan_item.balance.amount_minor == 1500000
    assert loan_item.balance.availability_state == "current"
    
    # Verify loan details are present
    assert loan_item.loan_details is not None
    assert loan_item.loan_details.outstanding_balance_minor == 1500000
    assert loan_item.loan_details.next_repayment_amount_minor == 50000
    assert loan_item.loan_details.remaining_term_months == 30
    assert loan_item.loan_details.next_repayment_date is not None
    assert loan_item.payment_source_eligible is True


def test_get_accounts_overview_loan_unavailable_graceful_degradation(db_session):
    """Test loan with unavailable servicing shows graceful degradation (TC-ACCT-005, ADR-010)."""
    customer_id = uuid.UUID("00000000-0000-0000-0000-000000000003")
    
    read_model_service = Mock()
    mock_loan = AccountReadModel(
        id=uuid.uuid4(),
        customer_profile_ref_id=customer_id,
        account_system_reference="LOAN-TEST-002",
        account_type="loan",
        display_name="Personal Loan",
        masked_account_identifier="****3456",
        balance_amount_minor=None,
        balance_currency=None,
        balance_availability_state="unavailable",
        as_of_timestamp=None,
        freshness_status="unknown",
        freshness_breach_indicator=False,
        source_system_type="loan_servicing",
        provenance_reference="test-loan-prov",
        projection_updated_at=datetime.now(UTC),
        # Loan servicing unavailable - all fields NULL
        loan_outstanding_balance_minor=None,
        loan_next_repayment_date=None,
        loan_next_repayment_amount_minor=None,
        loan_remaining_term_months=None
    )
    read_model_service.get_accounts_for_customer.return_value = ([mock_loan], 1)
    
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
    
    # Verify graceful degradation
    assert result.total == 1
    loan_item = result.items[0]
    assert loan_item.account_type == "loan"
    assert loan_item.balance.amount_minor is None
    assert loan_item.balance.availability_state == "unavailable"
    assert loan_item.balance.display_text == "Balance unavailable"
    assert loan_item.item_state == "partial"
    assert loan_item.payment_source_eligible is False
    assert result.overview_state == "partial"
    
    # Loan details should be NULL but not raise error
    assert loan_item.loan_details is not None
    assert loan_item.loan_details.outstanding_balance_minor is None
    assert loan_item.loan_details.next_repayment_date is None
    assert loan_item.loan_details.next_repayment_amount_minor is None
    assert loan_item.loan_details.remaining_term_months is None


def test_get_accounts_overview_mixed_accounts_with_loan(db_session):
    """Test overview with mix of current account and loan (TC-ACCT-006)."""
    customer_id = uuid.UUID("00000000-0000-0000-0000-000000000003")
    
    read_model_service = Mock()
    mock_current = AccountReadModel(
        id=uuid.uuid4(),
        customer_profile_ref_id=customer_id,
        account_system_reference="ACC-TEST-001",
        account_type="current",
        display_name="Main Current",
        masked_account_identifier="****1234",
        balance_amount_minor=250000,
        balance_currency="GBP",
        balance_availability_state="current",
        as_of_timestamp=datetime.now(UTC) - timedelta(seconds=20),
        freshness_status="within_target",
        freshness_breach_indicator=False,
        source_system_type="core_banking",
        provenance_reference="test-current-prov",
        projection_updated_at=datetime.now(UTC),
        loan_outstanding_balance_minor=None,
        loan_next_repayment_date=None,
        loan_next_repayment_amount_minor=None,
        loan_remaining_term_months=None
    )
    
    mock_loan = AccountReadModel(
        id=uuid.uuid4(),
        customer_profile_ref_id=customer_id,
        account_system_reference="LOAN-TEST-001",
        account_type="loan",
        display_name="Personal Loan",
        masked_account_identifier="****3456",
        balance_amount_minor=1500000,
        balance_currency="GBP",
        balance_availability_state="current",
        as_of_timestamp=datetime.now(UTC) - timedelta(seconds=30),
        freshness_status="within_target",
        freshness_breach_indicator=False,
        source_system_type="loan_servicing",
        provenance_reference="test-loan-prov",
        projection_updated_at=datetime.now(UTC),
        loan_outstanding_balance_minor=1500000,
        loan_next_repayment_date=datetime.now(UTC) + timedelta(days=15),
        loan_next_repayment_amount_minor=50000,
        loan_remaining_term_months=30
    )
    
    read_model_service.get_accounts_for_customer.return_value = ([mock_current, mock_loan], 2)
    
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
    
    # Verify
    assert result.total == 2
    assert len(result.items) == 2
    
    # Current account should not have loan details
    current_item = next(item for item in result.items if item.account_type == "current")
    assert current_item.loan_details is None
    assert current_item.payment_source_eligible is True
    
    # Loan should have loan details
    loan_item = next(item for item in result.items if item.account_type == "loan")
    assert loan_item.loan_details is not None
    assert loan_item.loan_details.outstanding_balance_minor == 1500000
    assert loan_item.payment_source_eligible is True


def test_get_accounts_overview_loan_stale_balance(db_session):
    """Test loan with stale balance shows freshness indicator (TC-ACCT-007)."""
    customer_id = uuid.UUID("00000000-0000-0000-0000-000000000003")
    
    read_model_service = Mock()
    stale_time = datetime.now(UTC) - timedelta(hours=3)
    mock_loan = AccountReadModel(
        id=uuid.uuid4(),
        customer_profile_ref_id=customer_id,
        account_system_reference="LOAN-TEST-003",
        account_type="loan",
        display_name="Personal Loan",
        masked_account_identifier="****3456",
        balance_amount_minor=1500000,
        balance_currency="GBP",
        balance_availability_state="stale",
        as_of_timestamp=stale_time,
        freshness_status="breached",
        freshness_breach_indicator=True,
        source_system_type="loan_servicing",
        provenance_reference="test-loan-prov",
        projection_updated_at=stale_time,
        loan_outstanding_balance_minor=1500000,
        loan_next_repayment_date=datetime.now(UTC) + timedelta(days=15),
        loan_next_repayment_amount_minor=50000,
        loan_remaining_term_months=30
    )
    read_model_service.get_accounts_for_customer.return_value = ([mock_loan], 1)
    
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
    loan_item = result.items[0]
    assert loan_item.account_type == "loan"
    assert loan_item.balance.amount_minor == 1500000
    assert loan_item.balance.availability_state == "stale"
    assert "(may be out of date)" in loan_item.balance.display_text
    assert loan_item.freshness_status == "breached"
    assert "out of date" in loan_item.freshness_text.lower()
    assert loan_item.payment_source_eligible is False
    
    # Loan details still present but may be stale
    assert loan_item.loan_details is not None
    assert loan_item.loan_details.outstanding_balance_minor == 1500000


def test_get_accounts_overview_loan_no_next_repayment(db_session):
    """Test loan with no next repayment date (final payment made) (TC-ACCT-008)."""
    customer_id = uuid.UUID("00000000-0000-0000-0000-000000000003")
    
    read_model_service = Mock()
    mock_loan = AccountReadModel(
        id=uuid.uuid4(),
        customer_profile_ref_id=customer_id,
        account_system_reference="LOAN-TEST-004",
        account_type="loan",
        display_name="Personal Loan",
        masked_account_identifier="****3456",
        balance_amount_minor=0,
        balance_currency="GBP",
        balance_availability_state="current",
        as_of_timestamp=datetime.now(UTC) - timedelta(seconds=30),
        freshness_status="within_target",
        freshness_breach_indicator=False,
        source_system_type="loan_servicing",
        provenance_reference="test-loan-prov",
        projection_updated_at=datetime.now(UTC),
        loan_outstanding_balance_minor=0,
        loan_next_repayment_date=None,
        loan_next_repayment_amount_minor=None,
        loan_remaining_term_months=0
    )
    read_model_service.get_accounts_for_customer.return_value = ([mock_loan], 1)
    
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
    
    # Verify
    loan_item = result.items[0]
    assert loan_item.account_type == "loan"
    assert loan_item.balance.amount_minor == 0
    
    # Loan details with zero balance and no next payment
    assert loan_item.loan_details is not None
    assert loan_item.loan_details.outstanding_balance_minor == 0
    assert loan_item.loan_details.next_repayment_date is None
    assert loan_item.loan_details.next_repayment_amount_minor is None
    assert loan_item.loan_details.remaining_term_months == 0

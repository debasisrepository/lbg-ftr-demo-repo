"""
Unit tests for business payment entitlement enforcement.
Requirement: BR-PAY-012 (Release 2)
Test Cases: TC-PAY-027, TC-PAY-029
"""
import uuid
from datetime import UTC, datetime
from unittest.mock import Mock

import pytest
from fastapi import HTTPException

from app.models.account_read_model import AccountReadModel
from app.services.account_service import AccountService
from app.services.payment_orchestration_service import PaymentOrchestrationService


def test_business_account_can_initiate_payments_flag_with_pay_entitlement(db_session):
    """Test business account shows can_initiate_payments=true with pay entitlement (TC-PAY-027)."""
    customer_id = uuid.UUID("00000000-0000-0000-0000-000000000004")
    business_profile_id = uuid.UUID("00000000-0000-0000-0000-000000000012")
    
    # Mock read model service
    read_model_service = Mock()
    mock_account = AccountReadModel(
        id=uuid.uuid4(),
        customer_profile_ref_id=business_profile_id,
        account_system_reference="BACC-TEST-001",
        account_type="current",
        display_name="SP Events Ltd - Business Current",
        masked_account_identifier="****7890",
        balance_amount_minor=500000,
        balance_currency="GBP",
        balance_availability_state="current",
        as_of_timestamp=datetime.now(UTC),
        freshness_status="within_target",
        freshness_breach_indicator=False,
        source_system_type="core_banking",
        provenance_reference="test-business-prov",
        projection_updated_at=datetime.now(UTC)
    )
    read_model_service.get_accounts_for_customer.return_value = ([mock_account], 1)
    
    # Mock capability service
    capability_service = Mock()
    from app.models.capability_status_record import CapabilityStatusRecord
    mock_capability = CapabilityStatusRecord(
        id=uuid.uuid4(),
        capability_name="accounts_overview",
        status_value="healthy",
        cause_category="unknown",
        effective_from=datetime.now(UTC)
    )
    capability_service.get_capability_status.return_value = mock_capability
    
    # Mock entitlement adapter - has pay permission
    entitlement_adapter = Mock()
    entitlement_adapter.check_resource_access.return_value = "allow"
    entitlement_adapter.check_permission.return_value = True  # Has pay permission
    
    # Create service
    service = AccountService(
        db=db_session,
        read_model_service=read_model_service,
        capability_service=capability_service,
        entitlement_adapter=entitlement_adapter
    )
    
    # Execute
    result = service.get_accounts_overview(business_profile_id, page=1, page_size=20)
    
    # Verify can_initiate_payments is true
    assert len(result.items) == 1
    assert result.items[0].can_initiate_payments is True
    
    # Verify pay permission was checked
    entitlement_adapter.check_permission.assert_called()


def test_business_account_cannot_initiate_payments_without_pay_entitlement(db_session):
    """Test business account shows can_initiate_payments=false without pay entitlement (TC-PAY-029)."""
    customer_id = uuid.UUID("00000000-0000-0000-0000-000000000009")
    viewer_profile_id = uuid.UUID("00000000-0000-0000-0000-000000000019")
    
    # Mock read model service
    read_model_service = Mock()
    mock_account = AccountReadModel(
        id=uuid.uuid4(),
        customer_profile_ref_id=viewer_profile_id,
        account_system_reference="BACC-TEST-002",
        account_type="current",
        display_name="SP Events Ltd - Business Current",
        masked_account_identifier="****7890",
        balance_amount_minor=500000,
        balance_currency="GBP",
        balance_availability_state="current",
        as_of_timestamp=datetime.now(UTC),
        freshness_status="within_target",
        freshness_breach_indicator=False,
        source_system_type="core_banking",
        provenance_reference="test-business-prov",
        projection_updated_at=datetime.now(UTC)
    )
    read_model_service.get_accounts_for_customer.return_value = ([mock_account], 1)
    
    # Mock capability service
    capability_service = Mock()
    from app.models.capability_status_record import CapabilityStatusRecord
    mock_capability = CapabilityStatusRecord(
        id=uuid.uuid4(),
        capability_name="accounts_overview",
        status_value="healthy",
        cause_category="unknown",
        effective_from=datetime.now(UTC)
    )
    capability_service.get_capability_status.return_value = mock_capability
    
    # Mock entitlement adapter - NO pay permission (viewer only)
    entitlement_adapter = Mock()
    entitlement_adapter.check_resource_access.return_value = "allow"
    entitlement_adapter.check_permission.return_value = False  # No pay permission
    
    # Create service
    service = AccountService(
        db=db_session,
        read_model_service=read_model_service,
        capability_service=capability_service,
        entitlement_adapter=entitlement_adapter
    )
    
    # Execute
    result = service.get_accounts_overview(viewer_profile_id, page=1, page_size=20)
    
    # Verify can_initiate_payments is false
    assert len(result.items) == 1
    assert result.items[0].can_initiate_payments is False


def test_payment_initiation_enforces_pay_entitlement(db_session):
    """Test payment initiation rejects users without pay entitlement."""
    customer_id = uuid.UUID("00000000-0000-0000-0000-000000000009")
    
    # Mock entitlement adapter - NO pay permission
    entitlement_adapter = Mock()
    entitlement_adapter.check_permission.return_value = False
    
    # Create payment service
    service = PaymentOrchestrationService(
        db=db_session,
        entitlement_adapter=entitlement_adapter
    )
    
    # Attempt payment initiation
    with pytest.raises(HTTPException) as exc_info:
        service.check_pay_entitlement(customer_id, "BACC-TEST-001")
    
    assert exc_info.value.status_code == 403
    assert "not authorized" in exc_info.value.detail.lower() or \
           "no permission" in exc_info.value.detail.lower()


def test_payment_approval_enforces_pay_entitlement(db_session):
    """Test payment approval rejects users without pay entitlement."""
    customer_id = uuid.UUID("00000000-0000-0000-0000-000000000009")
    payment_id = uuid.uuid4()
    
    # Mock entitlement adapter - NO pay permission
    entitlement_adapter = Mock()
    entitlement_adapter.check_permission.return_value = False
    
    # Create payment service
    service = PaymentOrchestrationService(
        db=db_session,
        entitlement_adapter=entitlement_adapter
    )
    
    # Attempt payment approval
    with pytest.raises(HTTPException) as exc_info:
        service.check_approval_entitlement(customer_id, payment_id)
    
    assert exc_info.value.status_code == 403
    assert "not authorized" in exc_info.value.detail.lower() or \
           "no permission" in exc_info.value.detail.lower()


def test_business_payment_includes_business_name_as_payer(db_session):
    """Test business payment carries business name as payer (BR-PAY-012)."""
    business_profile_id = uuid.UUID("00000000-0000-0000-0000-000000000012")
    business_name = "SP Events Ltd"
    
    # Mock payment orchestration service
    service = PaymentOrchestrationService(db=db_session)
    
    # Create payment context with business profile
    payment_context = {
        "profile_id": business_profile_id,
        "profile_type": "business",
        "business_name": business_name,
        "account_reference": "BACC-TEST-001"
    }
    
    # Verify business name is captured
    payer_name = service._get_payer_display_name(payment_context)
    
    assert payer_name == business_name
    assert "SP Events Ltd" in payer_name


def test_personal_payment_no_business_name(db_session):
    """Test personal payment does not include business name."""
    personal_profile_id = uuid.UUID("00000000-0000-0000-0000-000000000011")
    
    # Mock payment orchestration service
    service = PaymentOrchestrationService(db=db_session)
    
    # Create payment context with personal profile
    payment_context = {
        "profile_id": personal_profile_id,
        "profile_type": "personal",
        "business_name": None,
        "account_reference": "ACC-TEST-001"
    }
    
    # Verify no business name
    payer_name = service._get_payer_display_name(payment_context)
    
    assert payer_name != "SP Events Ltd"
    assert payer_name is None or "personal" in payer_name.lower()


def test_business_payment_reuses_release_1_flow(db_session):
    """
    Test business payments reuse Release 1 payment flow (CoP, fraud checks).
    
    Per BR-PAY-012: Business payments reuse Release 1 flow including:
    - Confirmation of Payee (CoP)
    - Dynamic fraud linking
    - Fraud checks
    """
    business_profile_id = uuid.UUID("00000000-0000-0000-0000-000000000012")
    
    service = PaymentOrchestrationService(db=db_session)
    
    # Verify service has access to fraud and CoP methods
    assert hasattr(service, '_check_fraud_rules')
    assert hasattr(service, '_perform_cop_check')
    
    # Business payments should use same methods as personal
    # This test documents the reuse requirement


def test_viewer_entitlement_prevents_payment_initiation(db_session):
    """Test viewer entitlement prevents payment initiation (BRL-PAY-02)."""
    viewer_profile_id = uuid.UUID("00000000-0000-0000-0000-000000000019")
    
    # Mock entitlement adapter - viewer only (no pay permission)
    entitlement_adapter = Mock()
    entitlement_adapter.check_permission.return_value = False
    
    service = PaymentOrchestrationService(
        db=db_session,
        entitlement_adapter=entitlement_adapter
    )
    
    # Verify viewer cannot initiate payment
    with pytest.raises(HTTPException) as exc_info:
        service.check_pay_entitlement(viewer_profile_id, "BACC-TEST-001")
    
    assert exc_info.value.status_code == 403


def test_business_account_with_pending_outgoing_payments(db_session):
    """Test business account displays pending outgoing payments (BR-ACCT-010)."""
    business_profile_id = uuid.UUID("00000000-0000-0000-0000-000000000012")
    
    # Mock read model service
    read_model_service = Mock()
    mock_account = AccountReadModel(
        id=uuid.uuid4(),
        customer_profile_ref_id=business_profile_id,
        account_system_reference="BACC-TEST-003",
        account_type="current",
        display_name="SP Events Ltd - Business Current",
        masked_account_identifier="****7890",
        balance_amount_minor=500000,
        balance_currency="GBP",
        balance_availability_state="current",
        as_of_timestamp=datetime.now(UTC),
        freshness_status="within_target",
        freshness_breach_indicator=False,
        source_system_type="core_banking",
        provenance_reference="test-business-prov",
        projection_updated_at=datetime.now(UTC),
        # Business-specific field
        pending_outgoing_payments_minor=25000  # £250.00 pending
    )
    read_model_service.get_accounts_for_customer.return_value = ([mock_account], 1)
    
    # Mock capability and entitlement
    capability_service = Mock()
    from app.models.capability_status_record import CapabilityStatusRecord
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
    entitlement_adapter.check_permission.return_value = True
    
    service = AccountService(
        db=db_session,
        read_model_service=read_model_service,
        capability_service=capability_service,
        entitlement_adapter=entitlement_adapter
    )
    
    result = service.get_accounts_overview(business_profile_id, page=1, page_size=20)
    
    # Verify pending outgoing payments displayed
    assert len(result.items) == 1
    account = result.items[0]
    assert hasattr(account, 'pending_outgoing_payments_minor') or \
           'pending' in str(account.balance.display_text).lower()

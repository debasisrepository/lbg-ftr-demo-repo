"""Tests for approval service (BR-ACCT-010 dual authorization)"""
import uuid
from datetime import datetime

import pytest

from app.services.approval_service import ApprovalService


def test_create_sca_approval_with_dynamic_linking(db_session, seeded_data):
    """Test creating SCA approval with dynamic linking (BR-PAY security)"""
    service = ApprovalService(db_session)

    payment_order_id = uuid.uuid4()
    device_id = uuid.UUID("10000000-0000-0000-0000-000000000201")
    source_account_id = uuid.uuid5(uuid.NAMESPACE_DNS, "account:acc_current_001")
    payee_id = uuid.UUID("10000000-0000-0000-0000-000000000501")
    amount_minor = 10000
    currency_code = "GBP"
    payment_reference = "Test payment"

    approval = service.create_sca_approval(
        payment_order_id=payment_order_id,
        device_id=device_id,
        source_account_id=source_account_id,
        payee_id=payee_id,
        amount_minor=amount_minor,
        currency_code=currency_code,
        payment_reference=payment_reference,
        correlation_id="test_corr_sca"
    )

    assert approval is not None
    assert approval.sca_approval_id is not None
    assert approval.payment_order_id == payment_order_id
    assert approval.device_id == device_id
    assert approval.approval_method == "passcode"
    assert approval.approval_result == "approved"
    assert approval.dynamic_link_digest is not None
    assert approval.amount_minor_snapshot == amount_minor
    assert approval.currency_code_snapshot == currency_code
    assert approval.payment_reference_snapshot == payment_reference


def test_create_sca_approval_with_step_up(db_session, seeded_data):
    """Test creating SCA approval with step-up challenge"""
    service = ApprovalService(db_session)

    payment_order_id = uuid.uuid4()
    device_id = uuid.UUID("10000000-0000-0000-0000-000000000201")
    source_account_id = uuid.uuid5(uuid.NAMESPACE_DNS, "account:acc_current_001")
    payee_id = uuid.UUID("10000000-0000-0000-0000-000000000501")

    approval = service.create_sca_approval(
        payment_order_id=payment_order_id,
        device_id=device_id,
        source_account_id=source_account_id,
        payee_id=payee_id,
        amount_minor=50000,
        currency_code="GBP",
        payment_reference="High value payment",
        correlation_id="test_corr_stepup",
        step_up_challenge_ref="challenge_123"
    )

    assert approval.approval_method == "step_up_challenge"


def test_verify_dynamic_link_success(db_session, seeded_data):
    """Test verifying dynamic link matches payment parameters"""
    service = ApprovalService(db_session)

    payment_order_id = uuid.uuid4()
    device_id = uuid.UUID("10000000-0000-0000-0000-000000000201")
    source_account_id = uuid.uuid5(uuid.NAMESPACE_DNS, "account:acc_current_001")
    payee_id = uuid.UUID("10000000-0000-0000-0000-000000000501")
    amount_minor = 25000
    currency_code = "GBP"
    payment_reference = "Invoice 12345"

    # Create approval
    approval = service.create_sca_approval(
        payment_order_id=payment_order_id,
        device_id=device_id,
        source_account_id=source_account_id,
        payee_id=payee_id,
        amount_minor=amount_minor,
        currency_code=currency_code,
        payment_reference=payment_reference,
        correlation_id="test_corr_verify"
    )

    # Verify with same parameters
    is_valid = service.verify_dynamic_link(
        approval,
        source_account_id,
        payee_id,
        amount_minor,
        currency_code,
        payment_reference
    )

    assert is_valid is True


def test_verify_dynamic_link_amount_changed(db_session, seeded_data):
    """Test verifying dynamic link fails when amount is changed (malware protection)"""
    service = ApprovalService(db_session)

    payment_order_id = uuid.uuid4()
    device_id = uuid.UUID("10000000-0000-0000-0000-000000000201")
    source_account_id = uuid.uuid5(uuid.NAMESPACE_DNS, "account:acc_current_001")
    payee_id = uuid.UUID("10000000-0000-0000-0000-000000000501")
    original_amount = 10000
    currency_code = "GBP"
    payment_reference = "Test payment"

    # Create approval with original amount
    approval = service.create_sca_approval(
        payment_order_id=payment_order_id,
        device_id=device_id,
        source_account_id=source_account_id,
        payee_id=payee_id,
        amount_minor=original_amount,
        currency_code=currency_code,
        payment_reference=payment_reference,
        correlation_id="test_corr_tamper"
    )

    # Verify with different amount (simulating malware tampering)
    is_valid = service.verify_dynamic_link(
        approval,
        source_account_id,
        payee_id,
        99999,  # Changed amount
        currency_code,
        payment_reference
    )

    assert is_valid is False


def test_verify_dynamic_link_payee_changed(db_session, seeded_data):
    """Test verifying dynamic link fails when payee is changed"""
    service = ApprovalService(db_session)

    payment_order_id = uuid.uuid4()
    device_id = uuid.UUID("10000000-0000-0000-0000-000000000201")
    source_account_id = uuid.uuid5(uuid.NAMESPACE_DNS, "account:acc_current_001")
    original_payee_id = uuid.UUID("10000000-0000-0000-0000-000000000501")
    different_payee_id = uuid.UUID("10000000-0000-0000-0000-000000000502")

    # Create approval with original payee
    approval = service.create_sca_approval(
        payment_order_id=payment_order_id,
        device_id=device_id,
        source_account_id=source_account_id,
        payee_id=original_payee_id,
        amount_minor=10000,
        currency_code="GBP",
        payment_reference="Test payment",
        correlation_id="test_corr_payee"
    )

    # Verify with different payee
    is_valid = service.verify_dynamic_link(
        approval,
        source_account_id,
        different_payee_id,  # Changed payee
        10000,
        "GBP",
        "Test payment"
    )

    assert is_valid is False


def test_verify_dynamic_link_account_changed(db_session, seeded_data):
    """Test verifying dynamic link fails when source account is changed"""
    service = ApprovalService(db_session)

    payment_order_id = uuid.uuid4()
    device_id = uuid.UUID("10000000-0000-0000-0000-000000000201")
    original_account_id = uuid.uuid5(uuid.NAMESPACE_DNS, "account:acc_current_001")
    different_account_id = uuid.uuid5(uuid.NAMESPACE_DNS, "account:acc_savings_001")
    payee_id = uuid.UUID("10000000-0000-0000-0000-000000000501")

    # Create approval with original account
    approval = service.create_sca_approval(
        payment_order_id=payment_order_id,
        device_id=device_id,
        source_account_id=original_account_id,
        payee_id=payee_id,
        amount_minor=10000,
        currency_code="GBP",
        payment_reference="Test payment",
        correlation_id="test_corr_account"
    )

    # Verify with different account
    is_valid = service.verify_dynamic_link(
        approval,
        different_account_id,  # Changed account
        payee_id,
        10000,
        "GBP",
        "Test payment"
    )

    assert is_valid is False


def test_verify_dynamic_link_reference_changed(db_session, seeded_data):
    """Test verifying dynamic link fails when reference is changed"""
    service = ApprovalService(db_session)

    payment_order_id = uuid.uuid4()
    device_id = uuid.UUID("10000000-0000-0000-0000-000000000201")
    source_account_id = uuid.uuid5(uuid.NAMESPACE_DNS, "account:acc_current_001")
    payee_id = uuid.UUID("10000000-0000-0000-0000-000000000501")

    # Create approval with original reference
    approval = service.create_sca_approval(
        payment_order_id=payment_order_id,
        device_id=device_id,
        source_account_id=source_account_id,
        payee_id=payee_id,
        amount_minor=10000,
        currency_code="GBP",
        payment_reference="Original reference",
        correlation_id="test_corr_ref"
    )

    # Verify with different reference
    is_valid = service.verify_dynamic_link(
        approval,
        source_account_id,
        payee_id,
        10000,
        "GBP",
        "Changed reference"  # Changed reference
    )

    assert is_valid is False


def test_sca_approval_expiration_time(db_session, seeded_data):
    """Test SCA approval has 5-minute expiration window"""
    service = ApprovalService(db_session)

    payment_order_id = uuid.uuid4()
    device_id = uuid.UUID("10000000-0000-0000-0000-000000000201")
    source_account_id = uuid.uuid5(uuid.NAMESPACE_DNS, "account:acc_current_001")
    payee_id = uuid.UUID("10000000-0000-0000-0000-000000000501")

    approval = service.create_sca_approval(
        payment_order_id=payment_order_id,
        device_id=device_id,
        source_account_id=source_account_id,
        payee_id=payee_id,
        amount_minor=10000,
        currency_code="GBP",
        payment_reference="Test payment",
        correlation_id="test_corr_exp"
    )

    # Check expiration is set
    assert approval.expires_at is not None
    assert approval.approved_at is not None

    # Check expiration is approximately 5 minutes after approval
    time_diff = (approval.expires_at - approval.approved_at).total_seconds()
    assert 295 <= time_diff <= 305  # Allow 5 second tolerance

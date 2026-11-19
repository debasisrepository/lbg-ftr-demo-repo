"""Tests for CoP service"""
import uuid

from app.services.cop_service import CopService


def test_run_cop_check_match(db_session):
    """Test CoP check with matching name"""
    payee_id = uuid.uuid4()

    service = CopService()
    cop_check = service.run_cop_check(
        db=db_session,
        payee_id=payee_id,
        payee_name="Jamie Clarke",
        sort_code="12-34-56",
        account_number="12345678",
        trigger="new_payee"
    )

    assert cop_check.outcome == "match"
    assert cop_check.policy_treatment == "allow"
    assert cop_check.checked_name == "Jamie Clarke"


def test_run_cop_check_mismatch(db_session):
    """Test CoP check with mismatched name"""
    payee_id = uuid.uuid4()

    service = CopService()
    cop_check = service.run_cop_check(
        db=db_session,
        payee_id=payee_id,
        payee_name="Test Mismatch",
        sort_code="00-00-00",
        account_number="12345678",
        trigger="new_payee"
    )

    assert cop_check.outcome == "mismatch"
    assert cop_check.policy_treatment == "warn"  # Default policy
    assert cop_check.suggested_name == "TestMismatch Ltd"


def test_acknowledge_cop_result(db_session):
    """Test acknowledging CoP mismatch"""
    payee_id = uuid.uuid4()
    customer_id = uuid.uuid4()

    service = CopService()

    # Create CoP check
    cop_check = service.run_cop_check(
        db=db_session,
        payee_id=payee_id,
        payee_name="Test Mismatch",
        sort_code="00-00-00",
        account_number="12345678",
        trigger="new_payee"
    )
    db_session.commit()

    assert cop_check.customer_acknowledged_at is None

    # Acknowledge
    updated_cop = service.acknowledge_cop_result(db_session, payee_id, customer_id)

    assert updated_cop.customer_acknowledged_at is not None

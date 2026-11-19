"""Tests for payee service"""
import uuid

from app.services.payee_service import PayeeService


def test_create_payee(db_session):
    """Test creating a payee with CoP check"""
    customer_id = uuid.uuid4()
    profile_id = uuid.uuid4()

    service = PayeeService()
    payee, cop_check = service.create_payee(
        db=db_session,
        customer_id=customer_id,
        profile_id=profile_id,
        payee_name="Test Payee",
        sort_code="12-34-56",
        account_number="12345678",
        payee_type="personal"
    )

    assert payee.payee_name == "Test Payee"
    assert payee.sort_code == "12-34-56"
    assert payee.account_number_masked == "****5678"
    assert payee.status == "active"  # Stub CoP returns match
    assert cop_check.outcome == "match"


def test_get_payees_for_customer(db_session):
    """Test getting payees for customer"""
    customer_id = uuid.uuid4()
    profile_id = uuid.uuid4()

    service = PayeeService()

    # Create a payee
    payee, _ = service.create_payee(
        db=db_session,
        customer_id=customer_id,
        profile_id=profile_id,
        payee_name="Test Payee",
        sort_code="12-34-56",
        account_number="12345678",
        payee_type="personal"
    )
    db_session.commit()

    # Get payees
    payees = service.get_payees_for_customer(db_session, customer_id, profile_id)

    assert len(payees) == 1
    assert payees[0].payee_id == payee.payee_id


def test_update_payee_triggers_cop_check(db_session):
    """Test updating payee name triggers new CoP check"""
    customer_id = uuid.uuid4()
    profile_id = uuid.uuid4()

    service = PayeeService()

    # Create payee
    payee, cop_check1 = service.create_payee(
        db=db_session,
        customer_id=customer_id,
        profile_id=profile_id,
        payee_name="Original Name",
        sort_code="12-34-56",
        account_number="12345678",
        payee_type="personal"
    )
    db_session.commit()

    # Update payee name
    updated_payee, cop_check2 = service.update_payee(
        db=db_session,
        payee_id=payee.payee_id,
        customer_id=customer_id,
        payee_name="Updated Name"
    )

    assert updated_payee.payee_name == "Updated Name"
    assert cop_check2 is not None
    assert cop_check2.cop_check_id != cop_check1.cop_check_id

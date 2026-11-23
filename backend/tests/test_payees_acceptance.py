"""
Acceptance tests for FR-PAY-001: View and select saved payees
"""
import uuid
from datetime import UTC, datetime, timedelta

import pytest

from app.models.account_read_model import AccountReadModel
from app.models.capability_status_record import CapabilityStatusRecord
from app.models.customer_profile_ref import CustomerProfileRef
from app.models.payee import Payee


def test_fr_pay_001_saved_payees_presented(auth_client, db_session):
    """
    FR-PAY-001: Saved payees available to the customer are presented in a clear selection journey.
    
    Acceptance: Saved payees available to the customer are presented in a clear selection journey.
    """
    # Get authenticated customer
    customer = db_session.query(CustomerProfileRef).filter_by(
        customer_party_id="CUST-SYNTH-001"
    ).first()
    
    # Ensure capability is healthy
    db_session.query(CapabilityStatusRecord).filter_by(capability_name="saved_payees").delete()
    capability = CapabilityStatusRecord(
        id=uuid.uuid4(),
        capability_name="saved_payees",
        status_value="healthy",
        cause_category="unknown",
        effective_from=datetime.now(UTC)
    )
    db_session.add(capability)
    
    # Clear existing payees and add test payees
    db_session.query(Payee).filter_by(customer_profile_ref_id=customer.id).delete()
    
    payees_data = [
        {"name": "Jamie Clarke", "sort": "04-00-04", "masked": "****3321"},
        {"name": "Priya Patel", "sort": "60-83-71", "masked": "****7745"},
        {"name": "K Evans Lettings", "sort": "20-45-77", "masked": "****9842"},
    ]
    
    for payee_data in payees_data:
        payee = Payee(
            id=uuid.uuid4(),
            customer_profile_ref_id=customer.id,
            payee_name=payee_data["name"],
            payee_account_identifier="12345678",
            payee_sort_code=payee_data["sort"],
            masked_account_identifier=payee_data["masked"],
            payee_status="saved_active",
            activated_at=datetime.now(UTC) - timedelta(days=30)
        )
        db_session.add(payee)
    
    db_session.commit()
    
    # Act
    response = auth_client.get("/api/v1/payees")
    
    # Assert
    assert response.status_code == 200
    data = response.json()
    
    # Verify saved payees are presented
    assert len(data["items"]) == 3
    assert data["capability"]["status_value"] == "healthy"
    
    # Verify each payee has clear identifying information
    for item in data["items"]:
        assert "payee_id" in item
        assert "payee_name" in item
        assert "payee_sort_code" in item
        assert "masked_account_identifier" in item
        assert len(item["payee_name"]) > 0
        assert len(item["payee_sort_code"]) > 0


def test_fr_pay_001_selecting_payee_for_payment(auth_client, db_session):
    """
    FR-PAY-001: Selecting a saved payee takes the customer into payment entry for that payee.
    
    Acceptance: The API returns payee_id which can be used to initiate payment entry.
    """
    # Get authenticated customer
    customer = db_session.query(CustomerProfileRef).filter_by(
        customer_party_id="CUST-SYNTH-001"
    ).first()
    
    # Add a saved payee
    db_session.query(Payee).filter_by(customer_profile_ref_id=customer.id).delete()
    payee = Payee(
        id=uuid.uuid4(),
        customer_profile_ref_id=customer.id,
        payee_name="Jamie Clarke",
        payee_account_identifier="12345678",
        payee_sort_code="04-00-04",
        masked_account_identifier="****3321",
        payee_status="saved_active",
        activated_at=datetime.now(UTC)
    )
    db_session.add(payee)
    db_session.commit()
    
    # Act
    response = auth_client.get("/api/v1/payees")
    
    # Assert
    assert response.status_code == 200
    data = response.json()
    
    # Verify payee_id is returned for payment entry
    assert len(data["items"]) == 1
    assert "payee_id" in data["items"][0]
    payee_id = data["items"][0]["payee_id"]
    assert payee_id is not None
    # Verify it's a valid UUID format
    uuid.UUID(payee_id)


def test_fr_pay_001_unavailable_payee_not_selectable(auth_client, db_session):
    """
    FR-PAY-001: A payee not available to the customer cannot be selected through the saved-payee journey.
    
    Acceptance: Blocked payees are not returned in the list.
    """
    # Get authenticated customer
    customer = db_session.query(CustomerProfileRef).filter_by(
        customer_party_id="CUST-SYNTH-001"
    ).first()
    
    # Clear existing payees
    db_session.query(Payee).filter_by(customer_profile_ref_id=customer.id).delete()
    
    # Add one active and one blocked payee
    active_payee = Payee(
        id=uuid.uuid4(),
        customer_profile_ref_id=customer.id,
        payee_name="Active Payee",
        payee_account_identifier="12345678",
        payee_sort_code="04-00-04",
        masked_account_identifier="****1111",
        payee_status="saved_active",
        activated_at=datetime.now(UTC)
    )
    db_session.add(active_payee)
    
    blocked_payee = Payee(
        id=uuid.uuid4(),
        customer_profile_ref_id=customer.id,
        payee_name="Blocked Payee",
        payee_account_identifier="87654321",
        payee_sort_code="04-00-04",
        masked_account_identifier="****2222",
        payee_status="blocked",
        activated_at=datetime.now(UTC)
    )
    db_session.add(blocked_payee)
    
    db_session.commit()
    
    # Act
    response = auth_client.get("/api/v1/payees")
    
    # Assert
    assert response.status_code == 200
    data = response.json()
    
    # Verify only active payee is returned
    assert len(data["items"]) == 1
    assert data["items"][0]["payee_name"] == "Active Payee"


def test_fr_pay_001_unavailable_capability_message(auth_client, db_session):
    """
    FR-PAY-001: If saved payee data is unavailable, the app presents a clear capability-specific message.
    
    Acceptance: When capability is unavailable, returns empty list with clear message.
    """
    # Set capability to unavailable
    db_session.query(CapabilityStatusRecord).filter_by(capability_name="saved_payees").delete()
    capability = CapabilityStatusRecord(
        id=uuid.uuid4(),
        capability_name="saved_payees",
        status_value="unavailable",
        cause_category="dependency_outage",
        customer_message_code="saved_payees_unavailable",
        recovery_guidance_code="try_again_later",
        effective_from=datetime.now(UTC)
    )
    db_session.add(capability)
    db_session.commit()
    
    # Act
    response = auth_client.get("/api/v1/payees")
    
    # Assert
    assert response.status_code == 200
    data = response.json()
    
    # Verify empty list with capability message
    assert len(data["items"]) == 0
    assert data["capability"]["status_value"] == "unavailable"
    assert data["capability"]["customer_message"] is not None
    assert len(data["capability"]["customer_message"]) > 0
    assert "unavailable" in data["capability"]["customer_message"].lower()


def test_fr_acct_003_database_constraint_enforcement(db_session):
    """
    FR-ACCT-003: Database constraint ensures unavailable/unknown balance cannot be numeric.
    
    Acceptance: The ck_arm_amount_state constraint prevents storing numeric balance
    when availability_state is unavailable or unknown.
    """
    from sqlalchemy.exc import IntegrityError
    
    # Get or create customer for this test
    customer = db_session.query(CustomerProfileRef).filter_by(
        customer_party_id="CUST-SYNTH-001"
    ).first()
    
    if not customer:
        # Create test customer
        customer = CustomerProfileRef(
            id=uuid.UUID("00000000-0000-0000-0000-000000000001"),
            customer_party_id="CUST-SYNTH-001",
            ciam_subject_reference="ciam-subject-synth-001",
            display_name="Alex Taylor",
            profile_type="personal",
            release_scope_status="in_scope",
            is_active=True
        )
        db_session.add(customer)
        db_session.commit()
    
    # Attempt to create account with unavailable state but numeric balance
    invalid_account = AccountReadModel(
        id=uuid.uuid4(),
        customer_profile_ref_id=customer.id,
        account_system_reference="INVALID-TEST-001",
        account_type="current",
        display_name="Invalid Account",
        masked_account_identifier="****9999",
        balance_amount_minor=100000,  # Numeric balance
        balance_currency="GBP",
        balance_availability_state="unavailable",  # Unavailable state
        freshness_status="unknown",
        source_system_type="core_banking",
        provenance_reference="test-invalid",
        projection_updated_at=datetime.now(UTC)
    )
    db_session.add(invalid_account)
    
    # Assert: Database constraint should prevent this
    with pytest.raises(IntegrityError) as exc_info:
        db_session.commit()
    
    # Verify it's the correct constraint
    assert "ck_arm_amount_state" in str(exc_info.value)
    
    db_session.rollback()
    
    # Verify correct usage: unavailable with NULL balance
    valid_account = AccountReadModel(
        id=uuid.uuid4(),
        customer_profile_ref_id=customer.id,
        account_system_reference="VALID-TEST-001",
        account_type="current",
        display_name="Valid Account",
        masked_account_identifier="****8888",
        balance_amount_minor=None,  # NULL balance
        balance_currency=None,
        balance_availability_state="unavailable",
        freshness_status="unknown",
        source_system_type="core_banking",
        provenance_reference="test-valid",
        projection_updated_at=datetime.now(UTC)
    )
    db_session.add(valid_account)
    db_session.commit()  # Should succeed
    
    # Verify it was saved correctly
    saved = db_session.query(AccountReadModel).filter_by(
        account_system_reference="VALID-TEST-001"
    ).first()
    assert saved is not None
    assert saved.balance_amount_minor is None
    assert saved.balance_availability_state == "unavailable"

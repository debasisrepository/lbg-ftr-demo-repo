"""
Integration tests for GET /api/v1/payees
Requirement: FR-PAY-001
"""
import uuid
from datetime import UTC, datetime, timedelta

from app.models.capability_status_record import CapabilityStatusRecord
from app.models.customer_profile_ref import CustomerProfileRef
from app.models.payee import Payee
from app.models.sandbox_entitlement import SandboxEntitlement


def test_get_payees_success(auth_client, db_session):
    """Test GET /api/v1/payees returns saved payees."""
    # Get the authenticated customer (Alex Taylor from conftest)
    customer = db_session.query(CustomerProfileRef).filter_by(
        customer_party_id="CUST-SYNTH-001"
    ).first()
    assert customer is not None
    
    # Ensure entitlement exists for payees
    existing_entitlement = db_session.query(SandboxEntitlement).filter_by(
        customer_profile_ref_id=customer.id,
        resource_type="payee"
    ).first()
    
    if not existing_entitlement:
        entitlement = SandboxEntitlement(
            id=uuid.uuid4(),
            customer_profile_ref_id=customer.id,
            resource_type="payee",
            resource_reference="*",
            decision="allow"
        )
        db_session.add(entitlement)
        db_session.commit()
    
    # Ensure capability status exists
    existing_cap = db_session.query(CapabilityStatusRecord).filter_by(
        capability_name="saved_payees"
    ).first()
    
    if not existing_cap:
        capability = CapabilityStatusRecord(
            id=uuid.uuid4(),
            capability_name="saved_payees",
            status_value="healthy",
            cause_category="unknown",
            effective_from=datetime.now(UTC)
        )
        db_session.add(capability)
        db_session.commit()
    
    # Clear existing payees and add test payees for the customer
    db_session.query(Payee).filter_by(customer_profile_ref_id=customer.id).delete()
    
    payees_data = [
        {
            "payee_name": "Jamie Clarke",
            "payee_sort_code": "04-00-04",
            "masked_account_identifier": "****3321",
        },
        {
            "payee_name": "Priya Patel",
            "payee_sort_code": "60-83-71",
            "masked_account_identifier": "****7745",
        },
        {
            "payee_name": "K Evans Lettings",
            "payee_sort_code": "20-45-77",
            "masked_account_identifier": "****9842",
        },
    ]
    
    for payee_data in payees_data:
        payee = Payee(
            id=uuid.uuid4(),
            customer_profile_ref_id=customer.id,
            payee_name=payee_data["payee_name"],
            payee_account_identifier="12345678",
            payee_sort_code=payee_data["payee_sort_code"],
            masked_account_identifier=payee_data["masked_account_identifier"],
            payee_status="saved_active",
            activated_at=datetime.now(UTC) - timedelta(days=30),
            cop_outcome_category="match",
            cop_provider_reference=f"cop-ref-{payee_data['payee_name'].replace(' ', '-').lower()}",
            cop_checked_at=datetime.now(UTC) - timedelta(days=30),
            correlation_id="test-correlation-id"
        )
        db_session.add(payee)
    
    db_session.commit()
    
    # Act: GET /api/v1/payees
    response = auth_client.get("/api/v1/payees")
    
    # Assert
    assert response.status_code == 200
    data = response.json()
    
    assert "items" in data
    assert "total" in data
    assert "page" in data
    assert "page_size" in data
    assert "capability" in data
    
    assert len(data["items"]) == 3
    assert data["total"] == 3
    assert data["page"] == 1
    assert data["page_size"] == 20
    
    # Check capability
    assert data["capability"]["capability_name"] == "saved_payees"
    assert data["capability"]["status_value"] == "healthy"
    
    # Check first payee (sorted by name)
    payee_names = [item["payee_name"] for item in data["items"]]
    assert "Jamie Clarke" in payee_names
    assert "Priya Patel" in payee_names
    assert "K Evans Lettings" in payee_names
    
    # Verify payee structure
    first_payee = data["items"][0]
    assert "payee_id" in first_payee
    assert "payee_name" in first_payee
    assert "payee_sort_code" in first_payee
    assert "masked_account_identifier" in first_payee
    # Full account number should NEVER be in the response
    assert "payee_account_identifier" not in first_payee


def test_get_payees_pagination(auth_client, db_session):
    """Test pagination parameters work correctly."""
    # Get authenticated customer
    customer = db_session.query(CustomerProfileRef).filter_by(
        customer_party_id="CUST-SYNTH-001"
    ).first()
    
    # Clear existing payees and add exactly 3
    db_session.query(Payee).filter_by(customer_profile_ref_id=customer.id).delete()
    
    for i in range(3):
        payee = Payee(
            id=uuid.uuid4(),
            customer_profile_ref_id=customer.id,
            payee_name=f"Test Payee {i+1}",
            payee_account_identifier="12345678",
            payee_sort_code="04-00-04",
            masked_account_identifier=f"****000{i}",
            payee_status="saved_active",
            activated_at=datetime.now(UTC)
        )
        db_session.add(payee)
    
    db_session.commit()
    
    # Act: Request page 1 with page_size 2
    response = auth_client.get("/api/v1/payees?page=1&page_size=2")
    
    # Assert
    assert response.status_code == 200
    data = response.json()
    
    assert len(data["items"]) == 2
    assert data["total"] == 3
    assert data["page"] == 1
    assert data["page_size"] == 2


def test_get_payees_only_saved_active(auth_client, db_session):
    """Test that only saved_active payees are returned, not blocked ones."""
    # Get authenticated customer
    customer = db_session.query(CustomerProfileRef).filter_by(
        customer_party_id="CUST-SYNTH-001"
    ).first()
    
    # Clear existing payees
    db_session.query(Payee).filter_by(customer_profile_ref_id=customer.id).delete()
    
    # Add 1 saved_active and 1 blocked payee
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
    
    assert len(data["items"]) == 1
    assert data["total"] == 1
    assert data["items"][0]["payee_name"] == "Active Payee"


def test_get_payees_empty_list(auth_client, db_session):
    """Test customer with no saved payees returns empty list."""
    # Get authenticated customer
    customer = db_session.query(CustomerProfileRef).filter_by(
        customer_party_id="CUST-SYNTH-001"
    ).first()
    
    # Clear all payees
    db_session.query(Payee).filter_by(customer_profile_ref_id=customer.id).delete()
    db_session.commit()
    
    # Act
    response = auth_client.get("/api/v1/payees")
    
    # Assert
    assert response.status_code == 200
    data = response.json()
    
    assert len(data["items"]) == 0
    assert data["total"] == 0
    assert data["capability"]["capability_name"] == "saved_payees"


def test_get_payees_requires_authentication(client):
    """Test that endpoint requires authentication."""
    # Act: Request without auth
    response = client.get("/api/v1/payees")
    
    # Assert
    assert response.status_code == 401
    data = response.json()
    assert "detail" in data


def test_get_payees_validation_errors(auth_client):
    """Test validation of pagination parameters."""
    # Act: Invalid page (must be >= 1)
    response = auth_client.get("/api/v1/payees?page=0")
    
    # Assert
    assert response.status_code == 422
    
    # Act: Invalid page_size (must be <= 50)
    response = auth_client.get("/api/v1/payees?page_size=100")
    
    # Assert
    assert response.status_code == 422

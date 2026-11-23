"""
Integration tests for accounts endpoints.
Requirement: FR-ACCT-001, FR-ACCT-002, FR-ACCT-003
"""
import uuid
from datetime import UTC, datetime, timedelta

from app.models.account_read_model import AccountReadModel
from app.models.capability_status_record import CapabilityStatusRecord
from app.models.customer_profile_ref import CustomerProfileRef
from app.models.sandbox_entitlement import SandboxEntitlement


def test_get_accounts_requires_auth(client):
    """Test that GET /api/v1/accounts requires authentication."""
    response = client.get("/api/v1/accounts")
    assert response.status_code == 401


def test_get_accounts_success(auth_client, db_session):
    """Test GET /api/v1/accounts returns account overview."""
    # Setup: seed customer, accounts, capability status
    customer = db_session.query(CustomerProfileRef).first()
    
    # Check if entitlement exists, add if not (seed may have already created it)
    existing_entitlement = db_session.query(SandboxEntitlement).filter_by(
        customer_profile_ref_id=customer.id,
        resource_type="account",
        resource_reference="*"
    ).first()
    
    if not existing_entitlement:
        entitlement = SandboxEntitlement(
            id=uuid.uuid4(),
            customer_profile_ref_id=customer.id,
            resource_type="account",
            resource_reference="*",
            decision="allow"
        )
        db_session.add(entitlement)
    
    # Check if capability exists, add if not
    existing_capability = db_session.query(CapabilityStatusRecord).filter_by(
        capability_name="accounts_overview"
    ).first()
    
    if not existing_capability:
        capability = CapabilityStatusRecord(
            id=uuid.uuid4(),
            capability_name="accounts_overview",
            status_value="healthy",
            cause_category="unknown",
            effective_from=datetime.now(UTC)
        )
        db_session.add(capability)
    
    # Clear existing accounts and add test accounts
    db_session.query(AccountReadModel).filter_by(customer_profile_ref_id=customer.id).delete()
    db_session.commit()
    account1 = AccountReadModel(
        id=uuid.uuid4(),
        customer_profile_ref_id=customer.id,
        account_system_reference="ACC-TEST-001",
        account_type="current",
        display_name="Current Account",
        masked_account_identifier="****1234",
        balance_amount_minor=124836,
        balance_currency="GBP",
        balance_availability_state="current",
        as_of_timestamp=datetime.now(UTC) - timedelta(seconds=30),
        freshness_status="within_target",
        freshness_breach_indicator=False,
        source_system_type="core_banking",
        provenance_reference="test-prov-001",
        projection_updated_at=datetime.now(UTC)
    )
    db_session.add(account1)
    
    account2 = AccountReadModel(
        id=uuid.uuid4(),
        customer_profile_ref_id=customer.id,
        account_system_reference="ACC-TEST-002",
        account_type="savings",
        display_name="Savings Account",
        masked_account_identifier="****5678",
        balance_amount_minor=350000,
        balance_currency="GBP",
        balance_availability_state="current",
        as_of_timestamp=datetime.now(UTC) - timedelta(seconds=45),
        freshness_status="within_target",
        freshness_breach_indicator=False,
        source_system_type="core_banking",
        provenance_reference="test-prov-002",
        projection_updated_at=datetime.now(UTC)
    )
    db_session.add(account2)
    db_session.commit()
    
    # Execute
    response = auth_client.get("/api/v1/accounts")
    
    # Verify
    assert response.status_code == 200
    data = response.json()
    
    assert "items" in data
    assert "total" in data
    assert "page" in data
    assert "page_size" in data
    assert "overview_state" in data
    assert "capability" in data
    
    assert data["total"] == 2
    assert len(data["items"]) == 2
    assert data["page"] == 1
    assert data["page_size"] == 20
    assert data["overview_state"] == "complete"
    
    # Check first account
    item = data["items"][0]
    assert item["account_type"] == "current"
    assert item["display_name"] == "Current Account"
    assert item["balance"]["amount_minor"] == 124836
    assert item["balance"]["currency"] == "GBP"
    assert item["balance"]["availability_state"] == "current"
    assert item["freshness_status"] == "within_target"
    assert "freshness_text" in item
    assert item["item_state"] == "available"
    assert item["payment_source_eligible"] is True
    
    # Check capability
    assert data["capability"]["capability_name"] == "accounts_overview"
    assert data["capability"]["status_value"] == "healthy"


def test_get_accounts_with_unavailable_balance(auth_client, db_session):
    """Test account with unavailable balance returns NULL amount."""
    customer = db_session.query(CustomerProfileRef).first()
    
    # Entitlement and capability should exist from seed, skip if present
    existing_entitlement = db_session.query(SandboxEntitlement).filter_by(
        customer_profile_ref_id=customer.id,
        resource_type="account",
        resource_reference="*"
    ).first()
    
    if not existing_entitlement:
        entitlement = SandboxEntitlement(
            id=uuid.uuid4(),
            customer_profile_ref_id=customer.id,
            resource_type="account",
            resource_reference="*",
            decision="allow"
        )
        db_session.add(entitlement)
    
    existing_capability = db_session.query(CapabilityStatusRecord).filter_by(
        capability_name="accounts_overview"
    ).first()
    
    if not existing_capability:
        capability = CapabilityStatusRecord(
            id=uuid.uuid4(),
            capability_name="accounts_overview",
            status_value="healthy",
            cause_category="unknown",
            effective_from=datetime.now(UTC)
        )
        db_session.add(capability)
    
    # Clear existing accounts and add account with unavailable balance
    db_session.query(AccountReadModel).filter_by(customer_profile_ref_id=customer.id).delete()
    db_session.commit()
    account = AccountReadModel(
        id=uuid.uuid4(),
        customer_profile_ref_id=customer.id,
        account_system_reference="ACC-TEST-003",
        account_type="current",
        display_name="Unavailable Account",
        masked_account_identifier="****9012",
        balance_amount_minor=None,
        balance_currency=None,
        balance_availability_state="unavailable",
        as_of_timestamp=None,
        freshness_status="unknown",
        freshness_breach_indicator=False,
        source_system_type="core_banking",
        provenance_reference="test-prov-003",
        projection_updated_at=datetime.now(UTC)
    )
    db_session.add(account)
    db_session.commit()
    
    # Execute
    response = auth_client.get("/api/v1/accounts")
    
    # Verify
    assert response.status_code == 200
    data = response.json()
    
    assert data["total"] == 1
    item = data["items"][0]
    assert item["balance"]["amount_minor"] is None
    assert item["balance"]["currency"] is None
    assert item["balance"]["availability_state"] == "unavailable"
    assert "unavailable" in item["balance"]["display_text"].lower()
    assert item["item_state"] == "partial"
    assert item["payment_source_eligible"] is False
    assert data["overview_state"] == "partial"


def test_get_accounts_pagination(auth_client, db_session):
    """Test account pagination."""
    customer = db_session.query(CustomerProfileRef).first()
    
    # Entitlement and capability should exist from seed
    existing_entitlement = db_session.query(SandboxEntitlement).filter_by(
        customer_profile_ref_id=customer.id,
        resource_type="account",
        resource_reference="*"
    ).first()
    
    if not existing_entitlement:
        entitlement = SandboxEntitlement(
            id=uuid.uuid4(),
            customer_profile_ref_id=customer.id,
            resource_type="account",
            resource_reference="*",
            decision="allow"
        )
        db_session.add(entitlement)
    
    existing_capability = db_session.query(CapabilityStatusRecord).filter_by(
        capability_name="accounts_overview"
    ).first()
    
    if not existing_capability:
        capability = CapabilityStatusRecord(
            id=uuid.uuid4(),
            capability_name="accounts_overview",
            status_value="healthy",
            cause_category="unknown",
            effective_from=datetime.now(UTC)
        )
        db_session.add(capability)
    
    # Clear existing accounts and add 5 accounts
    db_session.query(AccountReadModel).filter_by(customer_profile_ref_id=customer.id).delete()
    db_session.commit()
    for i in range(5):
        account = AccountReadModel(
            id=uuid.uuid4(),
            customer_profile_ref_id=customer.id,
            account_system_reference=f"ACC-TEST-{i:03d}",
            account_type="current",
            display_name=f"Account {i}",
            masked_account_identifier=f"****{i:04d}",
            balance_amount_minor=100000 + i,
            balance_currency="GBP",
            balance_availability_state="current",
            as_of_timestamp=datetime.now(UTC),
            freshness_status="within_target",
            freshness_breach_indicator=False,
            source_system_type="core_banking",
            provenance_reference=f"test-prov-{i}",
            projection_updated_at=datetime.now(UTC)
        )
        db_session.add(account)
    db_session.commit()
    
    # Test page 1 with page_size=2
    response = auth_client.get("/api/v1/accounts?page=1&page_size=2")
    assert response.status_code == 200
    data = response.json()
    assert data["total"] == 5
    assert len(data["items"]) == 2
    assert data["page"] == 1
    assert data["page_size"] == 2
    
    # Test page 2
    response = auth_client.get("/api/v1/accounts?page=2&page_size=2")
    assert response.status_code == 200
    data = response.json()
    assert len(data["items"]) == 2
    assert data["page"] == 2


def test_get_capability_statuses(auth_client, db_session):
    """Test GET /api/v1/capability-statuses returns all 4 capabilities."""
    # Check/seed all 4 capability statuses (seed may have already created them)
    capabilities = ["accounts_overview", "saved_payees", "payments", "payment_status"]
    for cap_name in capabilities:
        existing = db_session.query(CapabilityStatusRecord).filter_by(
            capability_name=cap_name,
            effective_to=None
        ).first()
        
        if not existing:
            capability = CapabilityStatusRecord(
                id=uuid.uuid4(),
                capability_name=cap_name,
                status_value="healthy",
                cause_category="unknown",
                effective_from=datetime.now(UTC)
            )
            db_session.add(capability)
    db_session.commit()
    
    # Execute
    response = auth_client.get("/api/v1/capability-statuses")
    
    # Verify
    assert response.status_code == 200
    data = response.json()
    
    assert "items" in data
    assert "total" in data
    assert data["total"] == 4
    assert len(data["items"]) == 4
    
    # Check all capabilities present
    capability_names = [item["capability_name"] for item in data["items"]]
    assert set(capability_names) == set(capabilities)
    
    # Check structure
    for item in data["items"]:
        assert "capability_name" in item
        assert "status_value" in item
        assert "customer_message" in item
        assert "effective_from" in item


def test_get_capability_statuses_requires_auth(client):
    """Test that GET /api/v1/capability-statuses requires authentication."""
    response = client.get("/api/v1/capability-statuses")
    assert response.status_code == 401

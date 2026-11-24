"""Customers router integration tests."""
import uuid
from datetime import datetime, timezone

from app.models.users import User
from app.models.roles import RoleProfile, RoleAssignment
from app.models.customers import Customer, CustomerAccount
from app.core.security import hash_password


def test_get_customers_list(client, db_session):
    """Test GET /api/v1/customers."""
    now = datetime.now(timezone.utc)
    
    # Create user and role with view_customer permission
    role = RoleProfile(
        id=uuid.uuid4(),
        created_at=now,
        updated_at=now,
        role_code="analyst",
        role_label="Analyst",
        allowed_widgets_json={"codes": []},
        entitled_queue_states_json={"states": []},
        allowed_actions_json={"actions": ["customer.view"]},
        can_view_sensitive_fields=False,
        profile_status="active",
    )
    db_session.add(role)
    
    user = User(
        id=uuid.uuid4(),
        created_at=now,
        updated_at=now,
        username="analyst1",
        display_name="Analyst One",
        email="analyst1@example.com",
        password_hash=hash_password("analyst123"),
        status="active",
    )
    db_session.add(user)
    db_session.flush()
    
    assignment = RoleAssignment(
        id=uuid.uuid4(),
        created_at=now,
        updated_at=now,
        user_id=user.id,
        role_code="analyst",
        assignment_status="active",
    )
    db_session.add(assignment)
    
    # Create test customers
    customer1 = Customer(
        id=uuid.uuid4(),
        created_at=now,
        updated_at=now,
        sap_customer_ref="CUST001",
        customer_name="ABC Corp",
        regional_business_unit="UK",
        credit_status_indicator="normal",
        master_data_source="SAP",
    )
    db_session.add(customer1)
    
    customer2 = Customer(
        id=uuid.uuid4(),
        created_at=now,
        updated_at=now,
        sap_customer_ref="CUST002",
        customer_name="XYZ Ltd",
        regional_business_unit="US",
        credit_status_indicator="watch",
        master_data_source="SAP",
    )
    db_session.add(customer2)
    db_session.commit()
    
    # Login
    login_response = client.post(
        "/api/v1/auth/login",
        json={"username": "analyst1", "password": "analyst123"},
    )
    token = login_response.json()["access_token"]
    
    # Get customers list
    response = client.get(
        "/api/v1/customers",
        headers={"Authorization": f"Bearer {token}"},
    )
    
    assert response.status_code == 200
    data = response.json()
    assert "items" in data
    assert "total" in data
    assert data["total"] == 2
    assert len(data["items"]) == 2


def test_get_customer_view(client, db_session):
    """Test GET /api/v1/customers/{customer_id}/view."""
    now = datetime.now(timezone.utc)
    
    # Create user and role with view_customer permission
    role = RoleProfile(
        id=uuid.uuid4(),
        created_at=now,
        updated_at=now,
        role_code="analyst",
        role_label="Analyst",
        allowed_widgets_json={"codes": []},
        entitled_queue_states_json={"states": []},
        allowed_actions_json={"actions": ["customer.view"]},
        can_view_sensitive_fields=False,
        profile_status="active",
    )
    db_session.add(role)
    
    user = User(
        id=uuid.uuid4(),
        created_at=now,
        updated_at=now,
        username="analyst1",
        display_name="Analyst One",
        email="analyst1@example.com",
        password_hash=hash_password("analyst123"),
        status="active",
    )
    db_session.add(user)
    db_session.flush()
    
    assignment = RoleAssignment(
        id=uuid.uuid4(),
        created_at=now,
        updated_at=now,
        user_id=user.id,
        role_code="analyst",
        assignment_status="active",
    )
    db_session.add(assignment)
    
    # Create test customer with account
    customer = Customer(
        id=uuid.uuid4(),
        created_at=now,
        updated_at=now,
        sap_customer_ref="CUST001",
        customer_name="ABC Corp",
        regional_business_unit="UK",
        credit_status_indicator="normal",
        master_data_source="SAP",
    )
    db_session.add(customer)
    db_session.flush()
    
    account = CustomerAccount(
        id=uuid.uuid4(),
        created_at=now,
        updated_at=now,
        customer_id=customer.id,
        sap_account_ref="ACCT001",
        company_code="1000",
        currency_code="GBP",
        account_status="active",
    )
    db_session.add(account)
    db_session.commit()
    
    # Login
    login_response = client.post(
        "/api/v1/auth/login",
        json={"username": "analyst1", "password": "analyst123"},
    )
    token = login_response.json()["access_token"]
    
    # Get customer 360 view
    response = client.get(
        f"/api/v1/customers/{customer.id}/view",
        headers={"Authorization": f"Bearer {token}"},
    )
    
    assert response.status_code == 200
    data = response.json()
    assert "customer_id" in data
    assert data["customer_id"] == str(customer.id)
    assert "profile" in data
    assert "accounts" in data
    assert "invoices" in data
    # Verify section structure
    assert data["profile"]["status"] in ["available", "unavailable", "masked"]
    assert data["accounts"]["status"] in ["available", "unavailable", "masked"]


def test_get_customer_view_not_found(client, db_session):
    """Test GET /api/v1/customers/{customer_id}/view with non-existent customer."""
    now = datetime.now(timezone.utc)
    
    # Create user and role
    role = RoleProfile(
        id=uuid.uuid4(),
        created_at=now,
        updated_at=now,
        role_code="analyst",
        role_label="Analyst",
        allowed_widgets_json={"codes": []},
        entitled_queue_states_json={"states": []},
        allowed_actions_json={"actions": ["customer.view"]},
        can_view_sensitive_fields=False,
        profile_status="active",
    )
    db_session.add(role)
    
    user = User(
        id=uuid.uuid4(),
        created_at=now,
        updated_at=now,
        username="analyst1",
        display_name="Analyst One",
        email="analyst1@example.com",
        password_hash=hash_password("analyst123"),
        status="active",
    )
    db_session.add(user)
    db_session.flush()
    
    assignment = RoleAssignment(
        id=uuid.uuid4(),
        created_at=now,
        updated_at=now,
        user_id=user.id,
        role_code="analyst",
        assignment_status="active",
    )
    db_session.add(assignment)
    db_session.commit()
    
    # Login
    login_response = client.post(
        "/api/v1/auth/login",
        json={"username": "analyst1", "password": "analyst123"},
    )
    token = login_response.json()["access_token"]
    
    # Try to get non-existent customer
    fake_id = uuid.uuid4()
    response = client.get(
        f"/api/v1/customers/{fake_id}/view",
        headers={"Authorization": f"Bearer {token}"},
    )
    
    assert response.status_code == 404

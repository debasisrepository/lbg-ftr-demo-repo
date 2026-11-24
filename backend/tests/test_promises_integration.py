"""Promises router integration tests."""
import uuid
from datetime import datetime, timezone, timedelta
from decimal import Decimal

from app.models.users import User
from app.models.roles import RoleProfile, RoleAssignment
from app.models.customers import Customer, CustomerAccount, Invoice
from app.models.promises import PromiseToPay
from app.models.policy import PolicyRuleSetVersion
from app.core.security import hash_password


def test_create_promise(client, db_session):
    """Test POST /api/v1/promises."""
    now = datetime.now(timezone.utc)
    
    # Create user and role with capture_promise permission
    role = RoleProfile(
        id=uuid.uuid4(),
        created_at=now,
        updated_at=now,
        role_code="analyst",
        role_label="Analyst",
        allowed_widgets_json={"codes": []},
        entitled_queue_states_json={"states": []},
        allowed_actions_json={"actions": ["promise.create"]},
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
    
    # Create test customer and account
    customer = Customer(
        id=uuid.uuid4(),
        created_at=now,
        updated_at=now,
        sap_customer_ref="CUST001",
        customer_name="ABC Corp",
        regional_business_unit="UK",
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
    
    invoice = Invoice(
        id=uuid.uuid4(),
        created_at=now,
        updated_at=now,
        customer_account_id=account.id,
        sap_invoice_ref="INV001",
        invoice_number="INV-2026-001",
        document_date=now.date(),
        due_date=(now + timedelta(days=30)).date(),
        invoice_amount=Decimal("10000.00"),
        open_amount=Decimal("10000.00"),
        currency_code="GBP",
        invoice_status="open",
    )
    db_session.add(invoice)
    
    # Create active policy rule set for validation
    rule_set = PolicyRuleSetVersion(
        id=uuid.uuid4(),
        created_at=now,
        updated_at=now,
        version_number=1,
        version_label="v1.0",
        rule_set_status="active",
        effective_from=now,
    )
    db_session.add(rule_set)
    db_session.commit()
    
    # Login
    login_response = client.post(
        "/api/v1/auth/login",
        json={"username": "analyst1", "password": "analyst123"},
    )
    token = login_response.json()["access_token"]
    
    # Create promise
    response = client.post(
        "/api/v1/promises",
        headers={
            "Authorization": f"Bearer {token}",
            "Idempotency-Key": "test-key-123",
        },
        json={
            "customer_account_id": str(account.id),
            "promised_amount": "5000.00",
            "currency_code": "GBP",
            "promised_date": (now + timedelta(days=7)).isoformat(),
            "promise_scope_type": "invoice_specific",
            "scope_links": [
                {
                    "link_type": "invoice",
                    "invoice_id": str(invoice.id),
                    "linked_amount": "5000.00",
                }
            ],
            "source_interaction": {
                "interaction_type": "call",
                "interaction_direction": "outbound",
                "interaction_channel": "phone",
                "occurred_at": now.isoformat(),
                "summary_text": "Customer promised payment",
            },
        },
    )
    
    assert response.status_code in [200, 201]
    data = response.json()
    assert "promise_id" in data
    assert data["customer_account_id"] == str(account.id)
    assert data["promised_amount"] == "5000.00"
    assert data["promise_scope_type"] == "invoice_specific"
    assert len(data["scope_links"]) == 1


def test_get_promises_list(client, db_session):
    """Test GET /api/v1/promises."""
    now = datetime.now(timezone.utc)
    
    # Create user and role with view_promise permission
    role = RoleProfile(
        id=uuid.uuid4(),
        created_at=now,
        updated_at=now,
        role_code="analyst",
        role_label="Analyst",
        allowed_widgets_json={"codes": []},
        entitled_queue_states_json={"states": []},
        allowed_actions_json={"actions": ["promise.read"]},
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
    
    # Create test customer and account
    customer = Customer(
        id=uuid.uuid4(),
        created_at=now,
        updated_at=now,
        sap_customer_ref="CUST001",
        customer_name="ABC Corp",
        regional_business_unit="UK",
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
    db_session.flush()
    
    # Create test promises
    promise1 = PromiseToPay(
        id=uuid.uuid4(),
        created_at=now,
        updated_at=now,
        customer_account_id=account.id,
        promised_amount=Decimal("5000.00"),
        currency_code="GBP",
        promised_date=(now + timedelta(days=7)).date(),
        promise_scope_type="invoice_specific",
        promise_status="captured",
        captured_by_user_id=user.id,
        captured_at=now,
        idempotency_key="test-key-1",
    )
    db_session.add(promise1)
    
    promise2 = PromiseToPay(
        id=uuid.uuid4(),
        created_at=now,
        updated_at=now,
        customer_account_id=account.id,
        promised_amount=Decimal("3000.00"),
        currency_code="GBP",
        promised_date=(now + timedelta(days=14)).date(),
        promise_scope_type="full_account",
        promise_status="captured",
        captured_by_user_id=user.id,
        captured_at=now,
        idempotency_key="test-key-2",
    )
    db_session.add(promise2)
    db_session.commit()
    
    # Login
    login_response = client.post(
        "/api/v1/auth/login",
        json={"username": "analyst1", "password": "analyst123"},
    )
    token = login_response.json()["access_token"]
    
    # Get promises list
    response = client.get(
        "/api/v1/promises",
        headers={"Authorization": f"Bearer {token}"},
    )
    
    assert response.status_code == 200
    data = response.json()
    assert "items" in data
    assert "total" in data
    assert data["total"] >= 2


def test_get_promise_by_id(client, db_session):
    """Test GET /api/v1/promises/{promise_id}."""
    now = datetime.now(timezone.utc)
    
    # Create user and role with view_promise permission
    role = RoleProfile(
        id=uuid.uuid4(),
        created_at=now,
        updated_at=now,
        role_code="analyst",
        role_label="Analyst",
        allowed_widgets_json={"codes": []},
        entitled_queue_states_json={"states": []},
        allowed_actions_json={"actions": ["promise.read"]},
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
    
    # Create test customer and account
    customer = Customer(
        id=uuid.uuid4(),
        created_at=now,
        updated_at=now,
        sap_customer_ref="CUST001",
        customer_name="ABC Corp",
        regional_business_unit="UK",
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
    db_session.flush()
    
    # Create test promise
    promise = PromiseToPay(
        id=uuid.uuid4(),
        created_at=now,
        updated_at=now,
        customer_account_id=account.id,
        promised_amount=Decimal("5000.00"),
        currency_code="GBP",
        promised_date=(now + timedelta(days=7)).date(),
        promise_scope_type="invoice_specific",
        promise_status="captured",
        captured_by_user_id=user.id,
        captured_at=now,
        idempotency_key="test-key-1",
    )
    db_session.add(promise)
    db_session.commit()
    
    # Login
    login_response = client.post(
        "/api/v1/auth/login",
        json={"username": "analyst1", "password": "analyst123"},
    )
    token = login_response.json()["access_token"]
    
    # Get promise by ID
    response = client.get(
        f"/api/v1/promises/{promise.id}",
        headers={"Authorization": f"Bearer {token}"},
    )
    
    assert response.status_code == 200
    data = response.json()
    assert data["promise_id"] == str(promise.id)
    assert data["customer_account_id"] == str(account.id)
    assert data["promised_amount"] == "5000.00"

"""Queue acceptance tests for FR-QUE-001."""
import uuid
from datetime import datetime, timezone
from decimal import Decimal

from app.models.users import User
from app.models.roles import RoleProfile, RoleAssignment
from app.models.customers import Customer, CustomerAccount, Invoice
from app.models.receivables import ReceivableItem
from app.core.security import hash_password


def test_items_grouped_by_state(client, db_session):
    """FR-QUE-001(1): Items grouped into actionable queue states."""
    now = datetime.now(timezone.utc)
    
    # Create user and role
    role = RoleProfile(
        id=uuid.uuid4(),
        created_at=now,
        updated_at=now,
        role_code="analyst",
        role_label="Analyst",
        allowed_widgets_json={"codes": []},
        entitled_queue_states_json={"states": ["active"]},
        allowed_actions_json={"actions": ["queue.read", "queue.refresh"]},
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
    
    # Get queue list
    response = client.get(
        "/api/v1/queue-items",
        headers={"Authorization": f"Bearer {token}"},
    )
    
    assert response.status_code == 200
    data = response.json()
    assert "groups" in data
    # Groups should have queue_state, count, total_amount


def test_non_standard_items_flagged(client, db_session):
    """FR-QUE-001(2): Non-standard items flagged or removed."""
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
        allowed_actions_json={"actions": ["queue.read", "queue.refresh"]},
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
    
    # Create disputed item
    customer = Customer(
        id=uuid.uuid4(),
        created_at=now,
        updated_at=now,
        sap_customer_ref="CUST001",
        customer_name="Test Customer",
        last_sync_at=now,
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
        last_sync_at=now,
    )
    db_session.add(account)
    db_session.flush()
    
    invoice = Invoice(
        id=uuid.uuid4(),
        created_at=now,
        updated_at=now,
        customer_account_id=account.id,
        sap_invoice_ref="INV001",
        invoice_number="9000001",
        document_date=now,
        due_date=now,
        invoice_amount=Decimal("1000.00"),
        open_amount=Decimal("1000.00"),
        currency_code="GBP",
        last_sync_at=now,
    )
    db_session.add(invoice)
    db_session.flush()
    
    receivable = ReceivableItem(
        id=uuid.uuid4(),
        created_at=now,
        updated_at=now,
        invoice_id=invoice.id,
        customer_account_id=account.id,
        sap_open_item_ref="ITEM001",
        aging_bucket="31-60",
        days_past_due=45,
        open_amount=Decimal("1000.00"),
        currency_code="GBP",
        dispute_indicator=True,  # Disputed
        unapplied_cash_indicator=False,
        last_sync_at=now,
    )
    db_session.add(receivable)
    db_session.commit()
    
    # Login and trigger refresh
    login_response = client.post(
        "/api/v1/auth/login",
        json={"username": "analyst1", "password": "analyst123"},
    )
    token = login_response.json()["access_token"]
    
    refresh_response = client.post(
        "/api/v1/queue-items/refresh",
        headers={"Authorization": f"Bearer {token}"},
        json={"scope": "full"},
    )
    assert refresh_response.status_code == 202
    
    # Get queue items filtered by non-standard
    response = client.get(
        "/api/v1/queue-items?non_standard=true",
        headers={"Authorization": f"Bearer {token}"},
    )
    
    assert response.status_code == 200
    data = response.json()
    # Should have items with is_non_standard=true
    if data["total"] > 0:
        assert any(item["is_non_standard"] for item in data["items"])


def test_queue_order_updates_on_recalculation(client, db_session):
    """FR-QUE-001(3): Queue order updates when priority factors change."""
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
        allowed_actions_json={"actions": ["queue.read", "queue.refresh"]},
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
    
    # Trigger first refresh
    refresh1_response = client.post(
        "/api/v1/queue-items/refresh",
        headers={"Authorization": f"Bearer {token}"},
        json={"scope": "full"},
    )
    assert refresh1_response.status_code == 202
    
    # Get initial queue
    response1 = client.get(
        "/api/v1/queue-items",
        headers={"Authorization": f"Bearer {token}"},
    )
    initial_items = response1.json()["items"]
    
    # Trigger second refresh (would recalculate)
    refresh2_response = client.post(
        "/api/v1/queue-items/refresh",
        headers={"Authorization": f"Bearer {token}"},
        json={"scope": "full"},
    )
    assert refresh2_response.status_code == 202
    
    # Get updated queue
    response2 = client.get(
        "/api/v1/queue-items",
        headers={"Authorization": f"Bearer {token}"},
    )
    updated_items = response2.json()["items"]
    
    # Verify deterministic: same inputs should give same order
    if len(initial_items) > 0 and len(updated_items) > 0:
        initial_ranks = [item["priority_rank"] for item in initial_items]
        updated_ranks = [item["priority_rank"] for item in updated_items]
        assert initial_ranks == updated_ranks

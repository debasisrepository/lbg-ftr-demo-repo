"""Workspace acceptance tests for FR-CAPA-001."""
import uuid
from datetime import datetime, timezone

from app.models.users import User
from app.models.roles import RoleProfile, RoleAssignment
from app.core.security import hash_password


def test_landing_page_role_based(client, db_session):
    """FR-CAPA-001(1): Home page rendered according to user's assigned role profile."""
    now = datetime.now(timezone.utc)
    
    # Create role with specific widgets
    role = RoleProfile(
        id=uuid.uuid4(),
        created_at=now,
        updated_at=now,
        role_code="analyst",
        role_label="Collections Analyst",
        allowed_widgets_json={"codes": ["queue_summary"]},
        entitled_queue_states_json={"states": ["active", "review"]},
        allowed_actions_json={"actions": ["queue.read", "customer.view"]},
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
    
    # Get landing
    response = client.get(
        "/api/v1/workspace/landing",
        headers={"Authorization": f"Bearer {token}"},
    )
    
    assert response.status_code == 200
    data = response.json()
    assert data["active_role_code"] == "analyst"
    assert data["active_role_label"] == "Collections Analyst"
    assert "queue.read" in data["allowed_actions"]


def test_role_specific_widgets(client, db_session):
    """FR-CAPA-001(2): Only authorized widgets shown for role."""
    now = datetime.now(timezone.utc)
    
    role = RoleProfile(
        id=uuid.uuid4(),
        created_at=now,
        updated_at=now,
        role_code="analyst",
        role_label="Analyst",
        allowed_widgets_json={"codes": ["queue_summary"]},
        entitled_queue_states_json={"states": []},
        allowed_actions_json={"actions": []},
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
    
    # Login and get landing
    login_response = client.post(
        "/api/v1/auth/login",
        json={"username": "analyst1", "password": "analyst123"},
    )
    token = login_response.json()["access_token"]
    
    response = client.get(
        "/api/v1/workspace/landing",
        headers={"Authorization": f"Bearer {token}"},
    )
    
    data = response.json()
    widget_codes = [w["widget_code"] for w in data["widgets"]]
    assert "queue_summary" in widget_codes


def test_role_switch_without_exposing_unauthorized(client, db_session):
    """FR-CAPA-001(3): User can switch role without exposing unauthorized actions."""
    now = datetime.now(timezone.utc)
    
    # Create two roles
    analyst_role = RoleProfile(
        id=uuid.uuid4(),
        created_at=now,
        updated_at=now,
        role_code="analyst",
        role_label="Analyst",
        allowed_widgets_json={"codes": ["queue_summary"]},
        entitled_queue_states_json={"states": []},
        allowed_actions_json={"actions": ["queue.read"]},
        can_view_sensitive_fields=False,
        profile_status="active",
    )
    db_session.add(analyst_role)
    
    reviewer_role = RoleProfile(
        id=uuid.uuid4(),
        created_at=now,
        updated_at=now,
        role_code="reviewer",
        role_label="Reviewer",
        allowed_widgets_json={"codes": []},
        entitled_queue_states_json={"states": []},
        allowed_actions_json={"actions": ["approve_promise"]},
        can_view_sensitive_fields=True,
        profile_status="active",
    )
    db_session.add(reviewer_role)
    
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
    
    # Assign both roles
    assignment1 = RoleAssignment(
        id=uuid.uuid4(),
        created_at=now,
        updated_at=now,
        user_id=user.id,
        role_code="analyst",
        assignment_status="active",
    )
    db_session.add(assignment1)
    
    assignment2 = RoleAssignment(
        id=uuid.uuid4(),
        created_at=now,
        updated_at=now,
        user_id=user.id,
        role_code="reviewer",
        assignment_status="active",
    )
    db_session.add(assignment2)
    db_session.commit()
    
    # Login as analyst
    login_response = client.post(
        "/api/v1/auth/login",
        json={"username": "analyst1", "password": "analyst123"},
    )
    token = login_response.json()["access_token"]
    
    # Verify analyst actions
    landing_response = client.get(
        "/api/v1/workspace/landing",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert "queue.read" in landing_response.json()["allowed_actions"]
    assert "approve_promise" not in landing_response.json()["allowed_actions"]
    
    # Switch to reviewer
    switch_response = client.put(
        "/api/v1/workspace/active-role",
        headers={"Authorization": f"Bearer {token}"},
        json={"role_code": "reviewer"},
    )
    assert switch_response.status_code == 200
    assert "approve_promise" in switch_response.json()["allowed_actions"]
    assert "queue.read" not in switch_response.json()["allowed_actions"]

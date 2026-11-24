"""Auth integration tests."""
import uuid
from datetime import datetime, timezone

from app.models.users import User
from app.models.roles import RoleProfile, RoleAssignment
from app.core.security import hash_password


def test_login_endpoint(client, db_session):
    """Test POST /api/v1/auth/login."""
    now = datetime.now(timezone.utc)
    
    # Create user and role
    role = RoleProfile(
        id=uuid.uuid4(),
        created_at=now,
        updated_at=now,
        role_code="analyst",
        role_label="Analyst",
        allowed_widgets_json={"codes": ["queue_summary"]},
        entitled_queue_states_json={"states": ["active"]},
        allowed_actions_json={"actions": ["queue.read"]},
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
    response = client.post(
        "/api/v1/auth/login",
        json={"username": "analyst1", "password": "analyst123"},
    )
    
    assert response.status_code == 200
    data = response.json()
    assert "access_token" in data
    assert data["token_type"] == "Bearer"
    assert data["user"]["username"] == "analyst1"
    assert data["active_role_code"] == "analyst"


def test_logout_endpoint(client, db_session):
    """Test POST /api/v1/auth/logout."""
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
    
    # Login
    login_response = client.post(
        "/api/v1/auth/login",
        json={"username": "analyst1", "password": "analyst123"},
    )
    token = login_response.json()["access_token"]
    
    # Logout
    response = client.post(
        "/api/v1/auth/logout",
        headers={"Authorization": f"Bearer {token}"},
    )
    
    assert response.status_code == 200
    data = response.json()
    assert "session_id" in data
    assert "revoked_at" in data


def test_session_endpoint(client, db_session):
    """Test GET /api/v1/auth/session."""
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
    
    # Login
    login_response = client.post(
        "/api/v1/auth/login",
        json={"username": "analyst1", "password": "analyst123"},
    )
    token = login_response.json()["access_token"]
    
    # Get session
    response = client.get(
        "/api/v1/auth/session",
        headers={"Authorization": f"Bearer {token}"},
    )
    
    assert response.status_code == 200
    data = response.json()
    assert data["user"]["username"] == "analyst1"
    assert data["active_role_code"] == "analyst"
    assert "seconds_until_inactivity_timeout" in data

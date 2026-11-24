"""Audit events router integration tests."""
import uuid
from datetime import datetime, timezone

from app.models.users import User
from app.models.roles import RoleProfile, RoleAssignment
from app.models.audit import AuditEvent
from app.core.security import hash_password


def test_get_audit_events(client, db_session):
    """Test GET /api/v1/audit-events."""
    now = datetime.now(timezone.utc)
    
    # Create user and role with audit.read permission
    role = RoleProfile(
        id=uuid.uuid4(),
        created_at=now,
        updated_at=now,
        role_code="analyst",
        role_label="Analyst",
        allowed_widgets_json={"codes": []},
        entitled_queue_states_json={"states": []},
        allowed_actions_json={"actions": ["audit.read"]},
        can_view_sensitive_fields=False,
        profile_status="active",
    )
    db_session.add(role)
    
    user = User(
        id=uuid.uuid4(),
        created_at=now,
        updated_at=now,
        username="audit_test_user1",
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
    
    # Create audit events (correlation_id is required, event_payload_json defaults to {})
    # Use valid event types from CHECK constraint
    event1 = AuditEvent(
        id=uuid.uuid4(),
        created_at=now,
        updated_at=now,
        event_type="promise_created",
        severity="info",
        actor_user_id=user.id,
        actor_role_code="analyst",
        affected_entity_type="promise_to_pay",
        affected_entity_id=uuid.uuid4(),
        correlation_id="correlation-123",
        event_timestamp=now,
        rationale_text="Promise recorded for invoice payment",
        event_payload_json={},
    )
    db_session.add(event1)
    
    event2 = AuditEvent(
        id=uuid.uuid4(),
        created_at=now,
        updated_at=now,
        event_type="promise_rejected",
        severity="warning",
        actor_user_id=user.id,
        actor_role_code="analyst",
        affected_entity_type="promise_to_pay",
        affected_entity_id=uuid.uuid4(),
        correlation_id="correlation-456",
        event_timestamp=now,
        rationale_text="Promise validation failed",
        event_payload_json={},
    )
    db_session.add(event2)
    db_session.commit()
    
    # Login
    login_response = client.post(
        "/api/v1/auth/login",
        json={"username": "audit_test_user1", "password": "analyst123"},
    )
    token = login_response.json()["access_token"]
    
    # Get audit events
    response = client.get(
        "/api/v1/audit-events",
        headers={"Authorization": f"Bearer {token}"},
    )
    
    assert response.status_code == 200
    data = response.json()
    assert "items" in data
    assert "total" in data
    assert data["total"] >= 2


def test_get_audit_events_filtered_by_type(client, db_session):
    """Test GET /api/v1/audit-events with event_type filter."""
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
        allowed_actions_json={"actions": ["audit.read"]},
        can_view_sensitive_fields=False,
        profile_status="active",
    )
    db_session.add(role)
    
    user = User(
        id=uuid.uuid4(),
        created_at=now,
        updated_at=now,
        username="audit_test_user1",
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
    
    # Create audit events of different types
    event_promise = AuditEvent(
        id=uuid.uuid4(),
        created_at=now,
        updated_at=now,
        event_type="promise_created",
        severity="info",
        actor_user_id=user.id,
        actor_role_code="analyst",
        affected_entity_type="promise_to_pay",
        affected_entity_id=uuid.uuid4(),
        correlation_id="correlation-promise",
        event_timestamp=now,
        event_payload_json={},
    )
    db_session.add(event_promise)
    
    event_policy = AuditEvent(
        id=uuid.uuid4(),
        created_at=now,
        updated_at=now,
        event_type="policy_evaluated",
        severity="warning",
        actor_user_id=user.id,
        actor_role_code="analyst",
        affected_entity_type="promise_to_pay",
        affected_entity_id=uuid.uuid4(),
        correlation_id="correlation-policy",
        event_timestamp=now,
        event_payload_json={},
    )
    db_session.add(event_policy)
    db_session.commit()
    
    # Login
    login_response = client.post(
        "/api/v1/auth/login",
        json={"username": "audit_test_user1", "password": "analyst123"},
    )
    token = login_response.json()["access_token"]
    
    # Get audit events filtered by type
    response = client.get(
        "/api/v1/audit-events?event_type=promise_created",
        headers={"Authorization": f"Bearer {token}"},
    )
    
    assert response.status_code == 200
    data = response.json()
    assert "items" in data
    # All returned items should be of type promise_created
    for item in data["items"]:
        assert item["event_type"] == "promise_created"


def test_get_audit_events_filtered_by_actor(client, db_session):
    """Test GET /api/v1/audit-events with actor_user_id filter."""
    now = datetime.now(timezone.utc)
    
    # Create users and role
    role = RoleProfile(
        id=uuid.uuid4(),
        created_at=now,
        updated_at=now,
        role_code="analyst",
        role_label="Analyst",
        allowed_widgets_json={"codes": []},
        entitled_queue_states_json={"states": []},
        allowed_actions_json={"actions": ["audit.read"]},
        can_view_sensitive_fields=False,
        profile_status="active",
    )
    db_session.add(role)
    
    user1 = User(
        id=uuid.uuid4(),
        created_at=now,
        updated_at=now,
        username="audit_test_user1",
        display_name="Analyst One",
        email="analyst1@example.com",
        password_hash=hash_password("analyst123"),
        status="active",
    )
    db_session.add(user1)
    
    user2 = User(
        id=uuid.uuid4(),
        created_at=now,
        updated_at=now,
        username="analyst2",
        display_name="Analyst Two",
        email="analyst2@example.com",
        password_hash=hash_password("analyst123"),
        status="active",
    )
    db_session.add(user2)
    db_session.flush()
    
    assignment1 = RoleAssignment(
        id=uuid.uuid4(),
        created_at=now,
        updated_at=now,
        user_id=user1.id,
        role_code="analyst",
        assignment_status="active",
    )
    db_session.add(assignment1)
    
    assignment2 = RoleAssignment(
        id=uuid.uuid4(),
        created_at=now,
        updated_at=now,
        user_id=user2.id,
        role_code="analyst",
        assignment_status="active",
    )
    db_session.add(assignment2)
    
    # Create audit events for different users
    event_user1 = AuditEvent(
        id=uuid.uuid4(),
        created_at=now,
        updated_at=now,
        event_type="promise_created",
        severity="info",
        actor_user_id=user1.id,
        actor_role_code="analyst",
        affected_entity_type="promise_to_pay",
        affected_entity_id=uuid.uuid4(),
        correlation_id="correlation-user1",
        event_timestamp=now,
        event_payload_json={},
    )
    db_session.add(event_user1)
    
    event_user2 = AuditEvent(
        id=uuid.uuid4(),
        created_at=now,
        updated_at=now,
        event_type="promise_created",
        severity="info",
        actor_user_id=user2.id,
        actor_role_code="analyst",
        affected_entity_type="promise_to_pay",
        affected_entity_id=uuid.uuid4(),
        correlation_id="correlation-user2",
        event_timestamp=now,
        event_payload_json={},
    )
    db_session.add(event_user2)
    db_session.commit()
    
    # Login as user1
    login_response = client.post(
        "/api/v1/auth/login",
        json={"username": "audit_test_user1", "password": "analyst123"},
    )
    token = login_response.json()["access_token"]
    
    # Get audit events filtered by user1
    response = client.get(
        f"/api/v1/audit-events?actor_user_id={user1.id}",
        headers={"Authorization": f"Bearer {token}"},
    )
    
    assert response.status_code == 200
    data = response.json()
    assert "items" in data
    # All returned items should be from user1
    for item in data["items"]:
        assert item["actor_user_id"] == str(user1.id)

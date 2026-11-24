"""Auth service unit tests."""
import uuid
from datetime import datetime, timedelta, timezone

import pytest

from app.core.clock import FixedClock
from app.core.errors import AuthenticationError, RateLimitError
from app.services.auth_service import AuthService
from app.repositories.user_repository import UserRepository
from app.models.users import User
from app.models.roles import RoleProfile, RoleAssignment
from app.core.security import hash_password


def test_login_success(db_session):
    """Test successful login."""
    now = datetime.now(timezone.utc)
    clock = FixedClock(now)
    
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
        username="testuser",
        display_name="Test User",
        email="test@example.com",
        password_hash=hash_password("password123"),
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
    auth_service = AuthService(db_session, clock)
    token, session = auth_service.login(
        username="testuser",
        password="password123",
        active_role_code="analyst",
        client_ip="127.0.0.1",
        correlation_id="test-123",
    )
    
    assert token is not None
    assert session.user_id == user.id
    assert session.active_role_code == "analyst"
    assert session.is_revoked is False


def test_login_invalid_password(db_session):
    """Test login with invalid password."""
    now = datetime.now(timezone.utc)
    clock = FixedClock(now)
    
    user = User(
        id=uuid.uuid4(),
        created_at=now,
        updated_at=now,
        username="testuser",
        display_name="Test User",
        email="test@example.com",
        password_hash=hash_password("password123"),
        status="active",
    )
    db_session.add(user)
    db_session.commit()
    
    auth_service = AuthService(db_session, clock)
    
    with pytest.raises(AuthenticationError) as exc_info:
        auth_service.login(
            username="testuser",
            password="wrongpassword",
            active_role_code="analyst",
            client_ip="127.0.0.1",
            correlation_id="test-123",
        )
    
    assert exc_info.value.code == "invalid_credentials"


def test_logout(db_session):
    """Test logout."""
    now = datetime.now(timezone.utc)
    clock = FixedClock(now)
    
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
        username="testuser",
        display_name="Test User",
        email="test@example.com",
        password_hash=hash_password("password123"),
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
    auth_service = AuthService(db_session, clock)
    token, session = auth_service.login(
        username="testuser",
        password="password123",
        active_role_code="analyst",
        client_ip="127.0.0.1",
        correlation_id="test-123",
    )
    
    # Logout
    revoked_session = auth_service.logout(token, "test-123")
    assert revoked_session.is_revoked is True
    assert revoked_session.revoke_reason == "user_logout"

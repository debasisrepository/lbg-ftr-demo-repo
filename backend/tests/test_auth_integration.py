"""Integration tests for auth endpoints."""
import pytest
from datetime import datetime, timezone
from app.models.auth import UserIdentity, RegisteredDevice
from app.models.profiles import UserProfile
from app.common.security import hash_password
from app.common.enums import UserStatus, ProfileType
from app.services.auth_service import rate_limiter


@pytest.fixture(autouse=True)
def reset_rate_limiter():
    """Reset rate limiter before each test."""
    rate_limiter.reset()
    yield
    rate_limiter.reset()


@pytest.fixture
def test_user_with_device(db_session):
    """Create test user with registered device."""
    now = datetime.now(timezone.utc)
    
    user = UserIdentity(
        external_identity_id="int-test-001",
        username="integration@example.com",
        hashed_password=hash_password("IntPass123!"),
        status=UserStatus.ACTIVE.value,
        created_at=now,
        updated_at=now
    )
    db_session.add(user)
    db_session.flush()
    
    profile = UserProfile(
        user_identity_id=user.id,
        profile_type=ProfileType.PERSONAL.value,
        display_name="Integration Test User",
        external_profile_id="profile-int-001",
        is_default=True,
        created_at=now,
        updated_at=now
    )
    db_session.add(profile)
    
    device = RegisteredDevice(
        user_identity_id=user.id,
        device_id="device-int-001",
        device_label="Test Device",
        public_key_ref="pubkey-int-001",
        biometric_enabled=True,
        passcode_enabled=True,
        created_at=now,
        updated_at=now
    )
    db_session.add(device)
    db_session.commit()
    
    return user, profile, device


def test_login_endpoint_success(client, test_user_with_device):
    """Test POST /api/v1/auth/login with valid credentials."""
    user, profile, device = test_user_with_device
    
    response = client.post(
        "/api/v1/auth/login",
        json={
            "username": "integration@example.com",
            "password": "IntPass123!"
        }
    )
    
    assert response.status_code == 200
    data = response.json()
    assert "access_token" in data
    assert data["token_type"] == "Bearer"
    assert data["step_up_required"] is True
    assert "passcode" in data["available_step_up_methods"]
    assert data["active_profile_id"] == profile.id


def test_login_endpoint_wrong_password(client, test_user_with_device):
    """Test POST /api/v1/auth/login with wrong password returns generic error."""
    response = client.post(
        "/api/v1/auth/login",
        json={
            "username": "integration@example.com",
            "password": "WrongPassword"
        }
    )
    
    assert response.status_code == 401
    data = response.json()
    assert "We couldn't sign you in with those details" in data["detail"]


def test_login_endpoint_user_not_found(client):
    """Test POST /api/v1/auth/login with non-existent user returns generic error."""
    response = client.post(
        "/api/v1/auth/login",
        json={
            "username": "nonexistent@example.com",
            "password": "AnyPassword"
        }
    )
    
    assert response.status_code == 401
    data = response.json()
    assert "We couldn't sign you in with those details" in data["detail"]


def test_login_endpoint_missing_fields(client):
    """Test POST /api/v1/auth/login with missing fields returns validation error."""
    response = client.post(
        "/api/v1/auth/login",
        json={
            "username": "test@example.com"
            # Missing password
        }
    )
    
    assert response.status_code == 422  # Validation error


def test_login_rate_limit(client, test_user_with_device, monkeypatch):
    """Test rate limiting on login endpoint."""
    # Enable rate limiting for this test
    from app.config import settings
    monkeypatch.setattr(settings, "rate_limit_enabled", True)
    monkeypatch.setattr(settings, "rate_limit_login_attempts", 5)
    monkeypatch.setattr(settings, "rate_limit_login_window_seconds", 300)
    
    # Attempt 5 failed logins
    for _ in range(5):
        response = client.post(
            "/api/v1/auth/login",
            json={
                "username": "integration@example.com",
                "password": "WrongPassword"
            }
        )
        assert response.status_code == 401
    
    # Next attempt should be rate limited
    response = client.post(
        "/api/v1/auth/login",
        json={
            "username": "integration@example.com",
            "password": "WrongPassword"
        }
    )
    
    assert response.status_code == 429
    data = response.json()
    assert "Too many sign-in attempts" in data["detail"]


def test_logout_endpoint(client, test_user_with_device):
    """Test POST /api/v1/auth/logout."""
    user, profile, device = test_user_with_device
    
    # First login
    login_response = client.post(
        "/api/v1/auth/login",
        json={
            "username": "integration@example.com",
            "password": "IntPass123!"
        }
    )
    assert login_response.status_code == 200
    token = login_response.json()["access_token"]
    
    # Logout
    logout_response = client.post(
        "/api/v1/auth/logout",
        headers={"Authorization": f"Bearer {token}"}
    )
    
    assert logout_response.status_code == 200
    data = logout_response.json()
    assert "message" in data


def test_logout_endpoint_unauthorized(client):
    """Test POST /api/v1/auth/logout without token returns 401."""
    response = client.post("/api/v1/auth/logout")
    
    assert response.status_code == 401

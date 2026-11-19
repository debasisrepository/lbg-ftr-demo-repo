"""Integration tests for SCA endpoints."""
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
def authenticated_user(client, db_session):
    """Create user and return authenticated client with session_id."""
    now = datetime.now(timezone.utc)
    
    user = UserIdentity(
        external_identity_id="sca-int-001",
        username="scaintegration@example.com",
        hashed_password=hash_password("ScaPass123!"),
        status=UserStatus.ACTIVE.value,
        created_at=now,
        updated_at=now
    )
    db_session.add(user)
    db_session.flush()
    
    profile = UserProfile(
        user_identity_id=user.id,
        profile_type=ProfileType.PERSONAL.value,
        display_name="SCA Test User",
        external_profile_id="profile-sca-int-001",
        is_default=True,
        created_at=now,
        updated_at=now
    )
    db_session.add(profile)
    
    device = RegisteredDevice(
        user_identity_id=user.id,
        device_id="device-sca-int-001",
        device_label="SCA Test Device",
        public_key_ref="pubkey-sca-int-001",
        biometric_enabled=True,
        passcode_enabled=True,
        created_at=now,
        updated_at=now
    )
    db_session.add(device)
    db_session.commit()
    
    # Login to get session
    login_response = client.post(
        "/api/v1/auth/login",
        json={
            "username": "scaintegration@example.com",
            "password": "ScaPass123!"
        }
    )
    assert login_response.status_code == 200
    session_id = login_response.json()["session_id"]
    
    return session_id, device.device_id


def test_verify_step_up_passcode_success(client, authenticated_user):
    """Test POST /api/v1/sca/verify-step-up with valid passcode."""
    session_id, device_id = authenticated_user
    
    response = client.post(
        "/api/v1/sca/verify-step-up",
        json={
            "session_id": session_id,
            "method": "passcode",
            "passcode": "123456",
            "device_id": device_id
        }
    )
    
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "verified"
    assert data["step_up_verified"] is True
    assert data["next_route"] == "/accounts"


def test_verify_step_up_passcode_failure(client, authenticated_user):
    """Test POST /api/v1/sca/verify-step-up with wrong passcode."""
    session_id, device_id = authenticated_user
    
    response = client.post(
        "/api/v1/sca/verify-step-up",
        json={
            "session_id": session_id,
            "method": "passcode",
            "passcode": "999999",  # Wrong but valid format
            "device_id": device_id
        }
    )
    
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "failed"
    assert data["step_up_verified"] is False
    assert data["remaining_attempts"] is not None
    assert data["remaining_attempts"] < 3


def test_verify_step_up_passcode_lockout(client, authenticated_user):
    """Test POST /api/v1/sca/verify-step-up locks after 3 failed attempts."""
    session_id, device_id = authenticated_user
    
    # Fail 3 times
    for i in range(3):
        response = client.post(
            "/api/v1/sca/verify-step-up",
            json={
                "session_id": session_id,
                "method": "passcode",
                "passcode": "999999",  # Wrong but valid format
                "device_id": device_id
            }
        )
        assert response.status_code == 200
        data = response.json()
        
        if i < 2:
            assert data["status"] == "failed"
        else:
            assert data["status"] == "locked"
            assert data["step_up_verified"] is False
            assert data["remaining_attempts"] == 0
            assert data["next_route"] == "/login"


def test_verify_step_up_biometric_success(client, authenticated_user):
    """Test POST /api/v1/sca/verify-step-up with valid biometric."""
    session_id, device_id = authenticated_user
    
    response = client.post(
        "/api/v1/sca/verify-step-up",
        json={
            "session_id": session_id,
            "method": "biometric",
            "biometric_assertion": "valid-biometric-token",
            "device_id": device_id
        }
    )
    
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "verified"
    assert data["step_up_verified"] is True
    assert data["next_route"] == "/accounts"


def test_verify_step_up_missing_passcode(client, authenticated_user):
    """Test POST /api/v1/sca/verify-step-up with missing passcode returns error."""
    session_id, device_id = authenticated_user
    
    response = client.post(
        "/api/v1/sca/verify-step-up",
        json={
            "session_id": session_id,
            "method": "passcode",
            # Missing passcode
            "device_id": device_id
        }
    )
    
    assert response.status_code == 400
    data = response.json()
    assert "Passcode required" in data["detail"]


def test_verify_step_up_invalid_method(client, authenticated_user):
    """Test POST /api/v1/sca/verify-step-up with invalid method returns validation error."""
    session_id, device_id = authenticated_user
    
    response = client.post(
        "/api/v1/sca/verify-step-up",
        json={
            "session_id": session_id,
            "method": "invalid_method",
            "passcode": "123456",
            "device_id": device_id
        }
    )
    
    assert response.status_code == 422  # Validation error

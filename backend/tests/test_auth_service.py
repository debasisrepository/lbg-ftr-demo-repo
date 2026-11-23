"""
Unit tests for AuthService with mocked repositories.
Requirement: FR-AUTH-003, FR-AUTH-006
"""
import uuid
from datetime import UTC, datetime, timedelta
from unittest.mock import Mock

import pytest
from fastapi import HTTPException

from app.models.customer_profile_ref import CustomerProfileRef
from app.models.device_registration import DeviceRegistration
from app.models.sandbox_credential import SandboxCredential
from app.models.user_session import UserSession
from app.schemas.auth_schemas import LoginRequest
from app.services.auth_service import AuthService


@pytest.fixture
def mock_db():
    """Mock database session."""
    db = Mock()
    db.commit = Mock()
    db.flush = Mock()
    return db


@pytest.fixture
def mock_auth_repo():
    """Mock authentication repository."""
    return Mock()


@pytest.fixture
def mock_ciam_adapter():
    """Mock CIAM adapter."""
    return Mock()


@pytest.fixture
def mock_entitlement_adapter():
    """Mock entitlement adapter."""
    return Mock()


@pytest.fixture
def auth_service(mock_db, mock_auth_repo, mock_ciam_adapter, mock_entitlement_adapter):
    """Create AuthService with mocked dependencies."""
    return AuthService(
        db=mock_db,
        auth_repo=mock_auth_repo,
        ciam_adapter=mock_ciam_adapter,
        entitlement_adapter=mock_entitlement_adapter
    )


@pytest.fixture
def sample_customer():
    """Sample customer profile."""
    return CustomerProfileRef(
        id=uuid.UUID("00000000-0000-0000-0000-000000000001"),
        customer_party_id="CUST-SYNTH-001",
        ciam_subject_reference="ciam-subject-synth-001",
        display_name="Alex Taylor",
        profile_type="personal",
        release_scope_status="in_scope",
        is_active=True,
        created_at=datetime.now(UTC),
        updated_at=datetime.now(UTC)
    )


@pytest.fixture
def sample_device():
    """Sample device registration."""
    return DeviceRegistration(
        id=uuid.uuid4(),
        customer_profile_ref_id=uuid.UUID("00000000-0000-0000-0000-000000000001"),
        device_identifier_hash="device-hash-test",
        mobile_platform="iOS",
        registration_status="active",
        ciam_subject_reference="ciam-subject-synth-001",
        registered_at=datetime.now(UTC) - timedelta(days=30),
        created_at=datetime.now(UTC),
        updated_at=datetime.now(UTC)
    )


@pytest.fixture
def sample_credential():
    """Sample sandbox credential."""
    return SandboxCredential(
        id=uuid.uuid4(),
        customer_profile_ref_id=uuid.UUID("00000000-0000-0000-0000-000000000001"),
        passcode_hash="$2b$12$test_hash",
        failed_attempt_count=0,
        created_at=datetime.now(UTC),
        updated_at=datetime.now(UTC)
    )


def test_login_success(
    auth_service,
    mock_auth_repo,
    mock_ciam_adapter,
    sample_customer,
    sample_device,
    sample_credential
):
    """Test successful login flow."""
    # Setup mocks
    mock_auth_repo.hash_device_identifier.return_value = "device-hash-test"
    mock_auth_repo.hash_client_address.return_value = "client-hash"
    mock_auth_repo.count_recent_auth_attempts_by_address.return_value = 0
    mock_auth_repo.get_device_by_identifier_hash.return_value = sample_device
    mock_auth_repo.get_customer_by_id.return_value = sample_customer
    mock_auth_repo.count_recent_auth_attempts_by_customer.return_value = 0
    mock_auth_repo.get_sandbox_credential.return_value = sample_credential
    mock_ciam_adapter.verify_passcode.return_value = True
    
    # Create mock session
    mock_session = Mock(spec=UserSession)
    mock_session.id = uuid.uuid4()
    mock_auth_repo.create_session.return_value = mock_session
    
    # Execute login
    request = LoginRequest(
        device_identifier="test-device-123",
        mobile_platform="iOS",
        passcode="Pass1234"
    )
    
    result = auth_service.login(request, "192.168.1.1", "test-correlation-id")
    
    # Assertions
    assert result.access_token is not None
    assert result.token_type == "Bearer"
    assert result.session_id == str(mock_session.id)
    assert result.user.id == str(sample_customer.id)
    assert result.user.display_name == sample_customer.display_name
    
    # Verify mocks were called
    mock_auth_repo.create_session.assert_called_once()
    mock_auth_repo.record_authentication_event.assert_called_once()


def test_login_unregistered_device(
    auth_service,
    mock_auth_repo
):
    """Test login fails for unregistered device."""
    # Setup mocks
    mock_auth_repo.hash_device_identifier.return_value = "device-hash-unknown"
    mock_auth_repo.hash_client_address.return_value = "client-hash"
    mock_auth_repo.count_recent_auth_attempts_by_address.return_value = 0
    mock_auth_repo.get_device_by_identifier_hash.return_value = None
    
    # Execute login
    request = LoginRequest(
        device_identifier="unknown-device",
        mobile_platform="iOS",
        passcode="Pass1234"
    )
    
    with pytest.raises(HTTPException) as exc_info:
        auth_service.login(request, "192.168.1.1", "test-correlation-id")
    
    assert exc_info.value.status_code == 401
    assert "couldn't sign you in" in exc_info.value.detail


def test_login_wrong_passcode(
    auth_service,
    mock_auth_repo,
    mock_ciam_adapter,
    sample_customer,
    sample_device,
    sample_credential
):
    """Test login fails for wrong passcode."""
    # Setup mocks
    mock_auth_repo.hash_device_identifier.return_value = "device-hash-test"
    mock_auth_repo.hash_client_address.return_value = "client-hash"
    mock_auth_repo.count_recent_auth_attempts_by_address.return_value = 0
    mock_auth_repo.get_device_by_identifier_hash.return_value = sample_device
    mock_auth_repo.get_customer_by_id.return_value = sample_customer
    mock_auth_repo.count_recent_auth_attempts_by_customer.return_value = 0
    mock_auth_repo.get_sandbox_credential.return_value = sample_credential
    mock_ciam_adapter.verify_passcode.return_value = False
    
    # Execute login
    request = LoginRequest(
        device_identifier="test-device-123",
        mobile_platform="iOS",
        passcode="WrongPass"
    )
    
    with pytest.raises(HTTPException) as exc_info:
        auth_service.login(request, "192.168.1.1", "test-correlation-id")
    
    assert exc_info.value.status_code == 401
    assert "couldn't sign you in" in exc_info.value.detail


def test_login_rate_limited_by_address(client, db_session):
    """Test login fails when rate limit exceeded for address - integration test."""
    # Enable rate limiting for this test
    from app.config import settings
    original_enabled = settings.rate_limit_enabled
    settings.rate_limit_enabled = True
    settings.rate_limit_login_per_address_max_attempts = 2
    
    try:
        # Make multiple login attempts to trigger rate limit
        for _ in range(3):
            response = client.post(
                "/api/v1/auth/login",
                json={
                    "device_identifier": "device-CUST-SYNTH-001-iOS",
                    "mobile_platform": "iOS",
                    "passcode": "Wrong999"  # Wrong passcode to trigger failures
                }
            )
        
        # The last one should be rate limited
        assert response.status_code == 429
        assert "Too many sign-in attempts" in response.json()["detail"]
    finally:
        # Restore settings
        settings.rate_limit_enabled = original_enabled


def test_validate_session_success(
    auth_service,
    mock_auth_repo,
    sample_customer
):
    """Test successful session validation."""
    # Create mock session
    mock_session = Mock(spec=UserSession)
    mock_session.id = uuid.uuid4()
    mock_session.customer_profile_ref_id = sample_customer.id
    mock_session.issued_at = datetime.now(UTC)
    mock_session.expires_at = datetime.now(UTC) + timedelta(hours=1)
    mock_session.last_activity_at = datetime.now(UTC) - timedelta(minutes=5)
    mock_session.revoked_at = None
    
    # Setup mocks
    mock_auth_repo.get_session_by_token_hash.return_value = mock_session
    mock_auth_repo.get_customer_by_id.return_value = sample_customer
    
    # Execute validation
    result = auth_service.validate_session("test-token", "test-correlation-id")
    
    # Assertions
    assert result.authenticated is True
    assert result.session_id == str(mock_session.id)
    assert result.user.id == str(sample_customer.id)
    
    # Verify activity was updated
    mock_auth_repo.update_session_activity.assert_called_once()


def test_validate_session_revoked(
    auth_service,
    mock_auth_repo
):
    """Test session validation fails for revoked session."""
    # Create mock revoked session
    mock_session = Mock(spec=UserSession)
    mock_session.revoked_at = datetime.now(UTC)
    
    # Setup mocks
    mock_auth_repo.get_session_by_token_hash.return_value = mock_session
    
    # Execute validation
    with pytest.raises(HTTPException) as exc_info:
        auth_service.validate_session("test-token", "test-correlation-id")
    
    assert exc_info.value.status_code == 401
    assert "revoked" in exc_info.value.detail


def test_validate_session_expired(
    auth_service,
    mock_auth_repo
):
    """Test session validation fails for expired session."""
    # Create mock expired session
    mock_session = Mock(spec=UserSession)
    mock_session.id = uuid.uuid4()
    mock_session.expires_at = datetime.now(UTC) - timedelta(hours=1)
    mock_session.last_activity_at = datetime.now(UTC) - timedelta(hours=2)
    mock_session.revoked_at = None
    
    # Setup mocks
    mock_auth_repo.get_session_by_token_hash.return_value = mock_session
    
    # Execute validation
    with pytest.raises(HTTPException) as exc_info:
        auth_service.validate_session("test-token", "test-correlation-id")
    
    assert exc_info.value.status_code == 401
    assert "expired" in exc_info.value.detail


def test_logout_success(
    auth_service,
    mock_auth_repo
):
    """Test successful logout."""
    # Create mock session
    mock_session = Mock(spec=UserSession)
    mock_session.id = uuid.uuid4()
    mock_session.revoked_at = None  # Not yet revoked
    
    # Setup mocks
    mock_auth_repo.get_session_by_token_hash.return_value = mock_session
    
    # Execute logout
    auth_service.logout("test-token", "test-correlation-id")
    
    # Verify session was revoked
    mock_auth_repo.revoke_session.assert_called_once_with(mock_session, "logout")


def test_logout_session_not_found(
    auth_service,
    mock_auth_repo
):
    """Test logout fails for nonexistent session."""
    # Setup mocks
    mock_auth_repo.get_session_by_token_hash.return_value = None
    
    # Execute logout
    with pytest.raises(HTTPException) as exc_info:
        auth_service.logout("test-token", "test-correlation-id")
    
    assert exc_info.value.status_code == 401
    assert "not found" in exc_info.value.detail

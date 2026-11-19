"""Unit tests for SCA service."""
import pytest
from datetime import datetime, timedelta, timezone
from app.services.sca_service import SCAService
from app.models.auth import UserIdentity, AuthSession, RegisteredDevice
from app.common.security import hash_password, create_access_token, hash_token
from app.common.enums import UserStatus, SessionState


@pytest.fixture
def test_user_and_session(db_session):
    """Create test user and session."""
    now = datetime.now(timezone.utc)
    
    user = UserIdentity(
        external_identity_id="sca-test-001",
        username="scatest@example.com",
        hashed_password=hash_password("TestPass123!"),
        status=UserStatus.ACTIVE.value,
        created_at=now,
        updated_at=now
    )
    db_session.add(user)
    db_session.flush()
    
    device = RegisteredDevice(
        user_identity_id=user.id,
        device_id="device-sca-001",
        device_label="Test Device",
        public_key_ref="pubkey-sca-001",
        biometric_enabled=True,
        passcode_enabled=True,
        created_at=now,
        updated_at=now
    )
    db_session.add(device)
    
    token = create_access_token(user.id, 60)
    token_hash = hash_token(token)
    
    session = AuthSession(
        user_identity_id=user.id,
        token_hash=token_hash,
        session_state=SessionState.ACTIVE.value,
        issued_at=now,
        expires_at=now + timedelta(minutes=60),
        last_activity_at=now,
        created_at=now,
        updated_at=now
    )
    db_session.add(session)
    db_session.commit()
    
    return user, session, device


@pytest.mark.asyncio
async def test_passcode_success(db_session, test_user_and_session):
    """Test successful passcode verification."""
    user, session, device = test_user_and_session
    
    sca_service = SCAService(db_session, "sca-test-001")
    
    result = await sca_service.verify_step_up(
        session_id=session.id,
        method="passcode",
        passcode="123456",  # Stub accepts this passcode
        device_id=device.device_id
    )
    
    assert result["status"] == "verified"
    assert result["step_up_verified"] is True
    assert result["next_route"] == "/accounts"


@pytest.mark.asyncio
async def test_passcode_failure(db_session, test_user_and_session):
    """Test failed passcode verification."""
    user, session, device = test_user_and_session
    
    sca_service = SCAService(db_session, "sca-test-002")
    
    result = await sca_service.verify_step_up(
        session_id=session.id,
        method="passcode",
        passcode="999999",  # Wrong but valid format
        device_id=device.device_id
    )
    
    assert result["status"] == "failed"
    assert result["step_up_verified"] is False
    assert result["remaining_attempts"] == 2


@pytest.mark.asyncio
async def test_passcode_lockout_after_three_attempts(db_session, test_user_and_session):
    """Test passcode lockout after 3 failed attempts."""
    user, session, device = test_user_and_session
    
    sca_service = SCAService(db_session, "sca-test-003")
    
    # First attempt - fail
    result1 = await sca_service.verify_step_up(
        session_id=session.id,
        method="passcode",
        passcode="999999",  # Wrong but valid format
        device_id=device.device_id
    )
    assert result1["status"] == "failed"
    assert result1["remaining_attempts"] == 2
    
    # Second attempt - fail
    result2 = await sca_service.verify_step_up(
        session_id=session.id,
        method="passcode",
        passcode="999999",  # Wrong but valid format
        device_id=device.device_id
    )
    assert result2["status"] == "failed"
    assert result2["remaining_attempts"] == 1
    
    # Third attempt - fail and lock
    result3 = await sca_service.verify_step_up(
        session_id=session.id,
        method="passcode",
        passcode="999999",  # Wrong but valid format
        device_id=device.device_id
    )
    assert result3["status"] == "locked"
    assert result3["step_up_verified"] is False
    assert result3["remaining_attempts"] == 0
    assert result3["next_route"] == "/login"


@pytest.mark.asyncio
async def test_biometric_success(db_session, test_user_and_session):
    """Test successful biometric verification."""
    user, session, device = test_user_and_session
    
    sca_service = SCAService(db_session, "sca-test-004")
    
    result = await sca_service.verify_step_up(
        session_id=session.id,
        method="biometric",
        biometric_assertion="valid-biometric-token",
        device_id=device.device_id
    )
    
    assert result["status"] == "verified"
    assert result["step_up_verified"] is True
    assert result["next_route"] == "/accounts"


@pytest.mark.asyncio
async def test_locked_challenge_returns_locked_status(db_session, test_user_and_session):
    """Test that already locked challenge returns locked status."""
    user, session, device = test_user_and_session
    
    sca_service = SCAService(db_session, "sca-test-005")
    
    # Lock the passcode by failing 3 times
    for _ in range(3):
        await sca_service.verify_step_up(
            session_id=session.id,
            method="passcode",
            passcode="999999",  # Wrong but valid format
            device_id=device.device_id
        )
    
    # Try again - should immediately return locked
    result = await sca_service.verify_step_up(
        session_id=session.id,
        method="passcode",
        passcode="123456",  # Even correct passcode won't work when locked
        device_id=device.device_id
    )
    
    assert result["status"] == "locked"
    assert result["step_up_verified"] is False
    assert result["next_route"] == "/login"

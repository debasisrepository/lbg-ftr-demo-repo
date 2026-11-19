"""Unit tests for auth service."""
import pytest
from datetime import datetime, timezone
from app.services.auth_service import AuthService, rate_limiter
from app.models.auth import UserIdentity
from app.models.profiles import UserProfile
from app.common.security import hash_password
from app.common.enums import UserStatus, ProfileType
from app.common.errors import AuthenticationError, RateLimitError


@pytest.fixture(autouse=True)
def reset_rate_limiter():
    """Reset rate limiter before each test."""
    rate_limiter.reset()
    yield
    rate_limiter.reset()


def test_login_success(db_session):
    """Test successful login."""
    now = datetime.now(timezone.utc)
    
    # Create user
    user = UserIdentity(
        external_identity_id="test-001",
        username="test@example.com",
        hashed_password=hash_password("TestPass123!"),
        status=UserStatus.ACTIVE.value,
        created_at=now,
        updated_at=now
    )
    db_session.add(user)
    db_session.commit()
    
    # Create profile
    profile = UserProfile(
        user_identity_id=user.id,
        profile_type=ProfileType.PERSONAL.value,
        display_name="Test User",
        external_profile_id="profile-test-001",
        is_default=True,
        created_at=now,
        updated_at=now
    )
    db_session.add(profile)
    db_session.commit()
    
    # Login
    auth_service = AuthService(db_session, "test-correlation-001")
    token, session_id, active_profile_id = auth_service.login(
        username="test@example.com",
        password="TestPass123!",
        client_ip="127.0.0.1"
    )
    
    assert token is not None
    assert session_id > 0
    assert active_profile_id == profile.id


def test_login_wrong_password(db_session):
    """Test login with wrong password returns generic error."""
    now = datetime.now(timezone.utc)
    
    user = UserIdentity(
        external_identity_id="test-002",
        username="test2@example.com",
        hashed_password=hash_password("CorrectPass123!"),
        status=UserStatus.ACTIVE.value,
        created_at=now,
        updated_at=now
    )
    db_session.add(user)
    db_session.commit()
    
    auth_service = AuthService(db_session, "test-correlation-002")
    
    with pytest.raises(AuthenticationError) as exc_info:
        auth_service.login(
            username="test2@example.com",
            password="WrongPassword",
            client_ip="127.0.0.1"
        )
    
    assert "We couldn't sign you in with those details" in str(exc_info.value)


def test_login_user_not_found(db_session):
    """Test login with non-existent user returns generic error."""
    auth_service = AuthService(db_session, "test-correlation-003")
    
    with pytest.raises(AuthenticationError) as exc_info:
        auth_service.login(
            username="nonexistent@example.com",
            password="AnyPassword",
            client_ip="127.0.0.1"
        )
    
    assert "We couldn't sign you in with those details" in str(exc_info.value)


def test_login_inactive_user(db_session):
    """Test login with suspended user returns generic error."""
    now = datetime.now(timezone.utc)
    
    user = UserIdentity(
        external_identity_id="test-004",
        username="suspended@example.com",
        hashed_password=hash_password("TestPass123!"),
        status=UserStatus.SUSPENDED.value,
        created_at=now,
        updated_at=now
    )
    db_session.add(user)
    db_session.commit()
    
    auth_service = AuthService(db_session, "test-correlation-004")
    
    with pytest.raises(AuthenticationError) as exc_info:
        auth_service.login(
            username="suspended@example.com",
            password="TestPass123!",
            client_ip="127.0.0.1"
        )
    
    assert "We couldn't sign you in with those details" in str(exc_info.value)


def test_login_rate_limit(db_session, monkeypatch):
    """Test rate limiting on login attempts."""
    # Enable rate limiting for this test
    from app.config import settings
    monkeypatch.setattr(settings, "rate_limit_enabled", True)
    monkeypatch.setattr(settings, "rate_limit_login_attempts", 5)
    monkeypatch.setattr(settings, "rate_limit_login_window_seconds", 300)
    
    now = datetime.now(timezone.utc)
    
    user = UserIdentity(
        external_identity_id="test-005",
        username="ratelimit@example.com",
        hashed_password=hash_password("TestPass123!"),
        status=UserStatus.ACTIVE.value,
        created_at=now,
        updated_at=now
    )
    db_session.add(user)
    db_session.commit()
    
    auth_service = AuthService(db_session, "test-correlation-005")
    
    # Attempt multiple failed logins (rate limit allows 5 attempts)
    for i in range(5):
        try:
            auth_service.login(
                username="ratelimit@example.com",
                password="WrongPassword",
                client_ip="192.168.1.100"
            )
        except AuthenticationError:
            pass  # Expected - wrong password
    
    # Next attempt should be rate limited (6th attempt)
    with pytest.raises(RateLimitError) as exc_info:
        auth_service.login(
            username="ratelimit@example.com",
            password="WrongPassword",
            client_ip="192.168.1.100"
        )
    
    assert "Too many sign-in attempts" in str(exc_info.value)


def test_logout(db_session):
    """Test logout revokes session."""
    now = datetime.now(timezone.utc)
    
    user = UserIdentity(
        external_identity_id="test-006",
        username="logout@example.com",
        hashed_password=hash_password("TestPass123!"),
        status=UserStatus.ACTIVE.value,
        created_at=now,
        updated_at=now
    )
    db_session.add(user)
    db_session.commit()
    
    profile = UserProfile(
        user_identity_id=user.id,
        profile_type=ProfileType.PERSONAL.value,
        display_name="Logout User",
        external_profile_id="profile-logout-001",
        is_default=True,
        created_at=now,
        updated_at=now
    )
    db_session.add(profile)
    db_session.commit()
    
    auth_service = AuthService(db_session, "test-correlation-006")
    
    # Login
    token, session_id, active_profile_id = auth_service.login(
        username="logout@example.com",
        password="TestPass123!",
        client_ip="127.0.0.1"
    )
    
    # Logout
    auth_service.logout(session_id, user.id)
    
    # Verify session is revoked
    session = auth_service.auth_repo.get_session_by_id(session_id)
    assert session.session_state == "revoked"

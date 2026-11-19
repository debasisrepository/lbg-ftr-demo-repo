"""Tests for entitlement service."""
from datetime import datetime, timezone
from app.services.entitlement_service import EntitlementService
from app.models.profiles import UserProfile, ProfileEntitlement
from app.models.auth import UserIdentity
from app.common.enums import UserStatus, ProfileType


def test_get_entitled_profiles(db_session):
    """Test getting entitled profiles for a user."""
    now = datetime.now(timezone.utc)
    
    # Create user
    user = UserIdentity(
        external_identity_id="test-user-001",
        username="test@example.com",
        hashed_password="hashed",
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
        display_name="Test Profile",
        business_name=None,
        external_profile_id="test-profile-001",
        is_default=True,
        created_at=now,
        updated_at=now
    )
    db_session.add(profile)
    db_session.commit()
    
    # Create entitlement
    ent = ProfileEntitlement(
        profile_id=profile.id,
        account_external_id="acc-001",
        can_view_accounts=True,
        can_create_payee=True,
        can_approve_payment=True,
        entitlement_source_version="v1.0",
        created_at=now,
        updated_at=now
    )
    db_session.add(ent)
    db_session.commit()
    
    # Test
    service = EntitlementService(db_session)
    profiles = service.get_entitled_profiles(user.id)
    
    assert len(profiles) == 1
    assert profiles[0]["profile_id"] == profile.id
    assert profiles[0]["can_view_accounts"] is True
    assert profiles[0]["can_create_payee"] is True
    assert profiles[0]["can_approve_payment"] is True


def test_check_profile_access(db_session):
    """Test checking profile access for a user."""
    now = datetime.now(timezone.utc)
    
    # Create user
    user = UserIdentity(
        external_identity_id="test-user-002",
        username="test2@example.com",
        hashed_password="hashed",
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
        display_name="Test Profile 2",
        business_name=None,
        external_profile_id="test-profile-002",
        is_default=True,
        created_at=now,
        updated_at=now
    )
    db_session.add(profile)
    db_session.commit()
    
    # Test
    service = EntitlementService(db_session)
    
    # User has access
    assert service.check_profile_access(profile.id, user.id) is True
    
    # Wrong user has no access
    assert service.check_profile_access(profile.id, user.id + 999) is False
    
    # Non-existent profile
    assert service.check_profile_access(999999, user.id) is False

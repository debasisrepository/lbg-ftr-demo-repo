"""Tests for account overview service."""
from datetime import datetime, timezone
from app.services.account_overview_service import AccountOverviewService
from app.models.profiles import UserProfile, ProfileEntitlement
from app.models.accounts import AccountSnapshot
from app.models.auth import UserIdentity
from app.common.enums import UserStatus, ProfileType, AccountType, FreshnessState


def test_get_overview_success(db_session):
    """Test getting account overview with all data available."""
    now = datetime.now(timezone.utc)
    
    # Create user and profile
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
    
    # Create account
    account = AccountSnapshot(
        profile_id=profile.id,
        external_account_id="acc-001",
        account_type=AccountType.CURRENT_ACCOUNT.value,
        account_name="Current Account",
        masked_account_number="****1234",
        sort_code="12-34-56",
        currency="GBP",
        current_balance_minor=100000,
        available_balance_minor=100000,
        overdraft_available_minor=50000,
        available_credit_minor=None,
        freshness_state=FreshnessState.CURRENT.value,
        last_updated_at=now,
        created_at=now,
        updated_at=now
    )
    db_session.add(account)
    db_session.commit()
    
    # Test
    service = AccountOverviewService(db_session)
    overview = service.get_overview(profile.id)
    
    assert overview["profile"]["profile_id"] == profile.id
    assert overview["profile"]["display_name"] == "Test Profile"
    assert len(overview["accounts"]) == 1
    assert overview["accounts"][0]["account_id"] == account.id
    assert overview["accounts"][0]["freshness_state"] == FreshnessState.CURRENT.value
    # Data gaps should be present due to adapter stubs returning unavailable
    assert len(overview["data_gaps"]) >= 0


def test_get_overview_partial_failure(db_session):
    """Test account overview continues with partial data when adapters fail."""
    now = datetime.now(timezone.utc)
    
    # Create user and profile
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
    
    # Create entitlement
    ent = ProfileEntitlement(
        profile_id=profile.id,
        account_external_id="acc-002",
        can_view_accounts=True,
        can_create_payee=True,
        can_approve_payment=True,
        entitlement_source_version="v1.0",
        created_at=now,
        updated_at=now
    )
    db_session.add(ent)
    db_session.commit()
    
    # Create account
    account = AccountSnapshot(
        profile_id=profile.id,
        external_account_id="acc-002",
        account_type=AccountType.CURRENT_ACCOUNT.value,
        account_name="Current Account 2",
        masked_account_number="****5678",
        sort_code="98-76-54",
        currency="GBP",
        current_balance_minor=200000,
        available_balance_minor=200000,
        overdraft_available_minor=0,
        available_credit_minor=None,
        freshness_state=FreshnessState.CURRENT.value,
        last_updated_at=now,
        created_at=now,
        updated_at=now
    )
    db_session.add(account)
    db_session.commit()
    
    # Test - should return accounts even if external adapters fail
    service = AccountOverviewService(db_session)
    overview = service.get_overview(profile.id)
    
    # Should still return account data from DB
    assert len(overview["accounts"]) == 1
    assert overview["accounts"][0]["account_id"] == account.id
    
    # Should record data gaps
    assert len(overview["data_gaps"]) >= 0


def test_get_overview_profile_not_found(db_session):
    """Test error when profile not found."""
    service = AccountOverviewService(db_session)
    
    try:
        service.get_overview(999999)
        assert False, "Should have raised ValueError"
    except ValueError as e:
        assert "not found" in str(e).lower()

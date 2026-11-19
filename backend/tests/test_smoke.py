"""Smoke tests to verify basic functionality."""
from datetime import datetime, timezone

from app.common.enums import UserStatus, ProfileType, AccountType
from app.common.security import hash_password, verify_password
from app.models.auth import UserIdentity
from app.models.profiles import UserProfile
from app.models.accounts import AccountSnapshot
from app.seed import seed_database


def test_health_endpoint(client):
    """Test the health check endpoint."""
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json() == {"status": "healthy"}


def test_api_health_endpoint(client):
    """Test the API health check endpoint."""
    response = client.get("/api/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "healthy"
    assert data["service"] == "lbg-ftr-demo-backend"


def test_password_hashing():
    """Test password hashing and verification."""
    password = "TestPassword123!"
    hashed = hash_password(password)
    
    # Password should be hashed
    assert hashed != password
    assert len(hashed) > 0
    
    # Verification should work
    assert verify_password(password, hashed) is True
    assert verify_password("WrongPassword", hashed) is False


def test_create_user(db_session):
    """Test creating a user in the database."""
    now = datetime.now(timezone.utc)
    
    user = UserIdentity(
        external_identity_id="test-001",
        username="test@example.com",
        hashed_password=hash_password("password123"),
        status=UserStatus.ACTIVE.value,
        created_at=now,
        updated_at=now
    )
    db_session.add(user)
    db_session.commit()
    
    # Verify user was created
    retrieved = db_session.query(UserIdentity).filter_by(username="test@example.com").first()
    assert retrieved is not None
    assert retrieved.external_identity_id == "test-001"
    assert retrieved.status == UserStatus.ACTIVE.value


def test_create_profile_and_account(db_session):
    """Test creating a profile and account."""
    now = datetime.now(timezone.utc)
    
    # Create user
    user = UserIdentity(
        external_identity_id="test-002",
        username="user@example.com",
        hashed_password=hash_password("password123"),
        status=UserStatus.ACTIVE.value,
        created_at=now,
        updated_at=now
    )
    db_session.add(user)
    db_session.flush()
    
    # Create profile
    profile = UserProfile(
        user_identity_id=user.id,
        profile_type=ProfileType.PERSONAL.value,
        display_name="Test User",
        business_name=None,
        external_profile_id="profile-test-002",
        is_default=True,
        created_at=now,
        updated_at=now
    )
    db_session.add(profile)
    db_session.flush()
    
    # Create account
    account = AccountSnapshot(
        profile_id=profile.id,
        external_account_id="acc-test-002",
        account_type=AccountType.CURRENT_ACCOUNT.value,
        account_name="Test Current Account",
        masked_account_number="****1234",
        sort_code="12-34-56",
        currency="GBP",
        current_balance_minor=100000,
        available_balance_minor=100000,
        overdraft_available_minor=0,
        available_credit_minor=None,
        freshness_state="current",
        last_updated_at=now,
        created_at=now,
        updated_at=now
    )
    db_session.add(account)
    db_session.commit()
    
    # Verify relationships
    retrieved_profile = db_session.query(UserProfile).filter_by(external_profile_id="profile-test-002").first()
    assert retrieved_profile is not None
    assert retrieved_profile.user_identity_id == user.id
    
    retrieved_account = db_session.query(AccountSnapshot).filter_by(external_account_id="acc-test-002").first()
    assert retrieved_account is not None
    assert retrieved_account.profile_id == profile.id
    assert retrieved_account.current_balance_minor == 100000


def test_seed_data_idempotency(db_session):
    """Test that seed data is idempotent."""
    # Run seed once
    seed_database(db_session)
    
    # Count users after first seed
    first_count = db_session.query(UserIdentity).count()
    assert first_count > 0
    
    # Run seed again
    seed_database(db_session)
    
    # Count should be the same
    second_count = db_session.query(UserIdentity).count()
    assert second_count == first_count


def test_seed_data_creates_admin(db_session):
    """Test that seed data creates admin user with correct credentials."""
    seed_database(db_session)
    
    # Verify admin user exists
    admin = db_session.query(UserIdentity).filter_by(username="admin@example.com").first()
    assert admin is not None
    assert admin.status == UserStatus.ACTIVE.value
    
    # Verify password
    assert verify_password("admin123", admin.hashed_password) is True


def test_seed_data_creates_profiles(db_session):
    """Test that seed data creates profiles."""
    seed_database(db_session)
    
    # Should have at least 3 profiles (admin personal, personal user, business user)
    profiles = db_session.query(UserProfile).all()
    assert len(profiles) >= 3
    
    # Verify profile types exist
    personal_profiles = db_session.query(UserProfile).filter_by(profile_type=ProfileType.PERSONAL.value).all()
    assert len(personal_profiles) >= 2
    
    business_profiles = db_session.query(UserProfile).filter_by(profile_type=ProfileType.BUSINESS.value).all()
    assert len(business_profiles) >= 1


def test_seed_data_creates_accounts(db_session):
    """Test that seed data creates accounts."""
    seed_database(db_session)
    
    # Should have at least 5 accounts
    accounts = db_session.query(AccountSnapshot).all()
    assert len(accounts) >= 5
    
    # Verify different account types exist
    current_accounts = db_session.query(AccountSnapshot).filter_by(account_type=AccountType.CURRENT_ACCOUNT.value).all()
    assert len(current_accounts) >= 2
    
    credit_cards = db_session.query(AccountSnapshot).filter_by(account_type=AccountType.CREDIT_CARD.value).all()
    assert len(credit_cards) >= 1

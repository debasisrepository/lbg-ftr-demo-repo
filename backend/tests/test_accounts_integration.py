"""Integration tests for accounts endpoints."""
from datetime import datetime, timezone
from app.models.profiles import UserProfile, ProfileEntitlement
from app.models.accounts import AccountSnapshot
from app.common.enums import ProfileType, AccountType, FreshnessState


def test_get_account_overview(auth_client, db_session):
    """Test GET /api/v1/accounts/overview returns account list."""
    now = datetime.now(timezone.utc)
    
    # Get the test user's profile (auth_client is logged in as admin@example.com -> "Admin User")
    profile = db_session.query(UserProfile).filter_by(display_name="Admin User").first()
    assert profile is not None
    
    # Create entitlement
    ent = ProfileEntitlement(
        profile_id=profile.id,
        account_external_id="acc-test-001",
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
        external_account_id="acc-test-001",
        account_type=AccountType.CURRENT_ACCOUNT.value,
        account_name="Test Current Account",
        masked_account_number="****1234",
        sort_code="12-34-56",
        currency="GBP",
        current_balance_minor=124836,
        available_balance_minor=124836,
        overdraft_available_minor=0,
        available_credit_minor=None,
        freshness_state=FreshnessState.CURRENT.value,
        last_updated_at=now,
        created_at=now,
        updated_at=now
    )
    db_session.add(account)
    db_session.commit()
    
    # Test
    response = auth_client.get(f"/api/v1/accounts/overview?profile_id={profile.id}")
    assert response.status_code == 200
    
    data = response.json()
    assert "profile" in data
    assert "accounts" in data
    assert "data_gaps" in data
    assert data["profile"]["profile_id"] == profile.id
    assert len(data["accounts"]) >= 1
    
    # Check account has freshness_state
    for acc in data["accounts"]:
        assert "freshness_state" in acc
        assert "last_updated_at" in acc


def test_get_account_overview_wrong_profile(auth_client, db_session):
    """Test 403 when accessing another user's profile."""
    response = auth_client.get("/api/v1/accounts/overview?profile_id=999999")
    assert response.status_code == 403

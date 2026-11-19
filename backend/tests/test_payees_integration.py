"""Integration tests for payees endpoints."""
from datetime import datetime, timezone
from app.models.profiles import UserProfile
from app.models.payees import Payee, CoPResult
from app.models.sca import StepUpChallenge
from app.models.auth import AuthSession
from app.common.enums import (
    ProfileType, SessionState, ChallengeType,
    ChallengeMethod, ChallengeStatus, CoPResultCode, CoPDecisionState
)


def test_get_payees(auth_client, db_session):
    """Test GET /api/v1/payees returns payee list."""
    now = datetime.now(timezone.utc)
    
    # Get the test user's profile (auth_client is logged in as admin@example.com -> "Admin User")
    profile = db_session.query(UserProfile).filter_by(display_name="Admin User").first()
    assert profile is not None
    
    # Create payee
    payee = Payee(
        profile_id=profile.id,
        display_name="Jamie Clarke",
        nickname=None,
        sort_code="04-00-04",
        account_number_last4="3746",
        account_number_hash="hash123",
        can_proceed=True,
        created_in_journey=False,
        payee_action_sca_verified_at=now,
        created_at=now,
        updated_at=now
    )
    db_session.add(payee)
    db_session.commit()
    
    # Create CoP result
    cop = CoPResult(
        payee_id=payee.id,
        result_code=CoPResultCode.MATCH.value,
        decision_state=CoPDecisionState.CONFIRMED.value,
        provider_reference="cop-ref-001",
        returned_name="Jamie Clarke",
        warning_message=None,
        checked_at=now,
        override_confirmed_at=None,
        created_at=now,
        updated_at=now
    )
    db_session.add(cop)
    db_session.commit()
    
    # Test
    response = auth_client.get(f"/api/v1/payees?profile_id={profile.id}")
    assert response.status_code == 200
    
    data = response.json()
    assert "payees" in data
    assert len(data["payees"]) >= 1
    
    # Check payee has required fields
    for p in data["payees"]:
        assert "payee_id" in p
        assert "display_name" in p
        assert "sort_code" in p
        assert "masked_account_number" in p
        assert "can_proceed" in p


def test_create_payee_with_sca(auth_client, db_session):
    """Test POST /api/v1/payees creates payee after SCA."""
    now = datetime.now(timezone.utc)
    
    # Get the test user's profile (auth_client is logged in as admin@example.com -> "Admin User")
    profile = db_session.query(UserProfile).filter_by(display_name="Admin User").first()
    assert profile is not None
    
    # Get the test user's session
    session = db_session.query(AuthSession).filter_by(active_profile_id=profile.id).first()
    assert session is not None
    
    # Create verified SCA challenge
    challenge = StepUpChallenge(
        auth_session_id=session.id,
        payment_instruction_id=None,
        challenge_type=ChallengeType.PAYEE_ACTION.value,
        method=ChallengeMethod.PASSCODE.value,
        status=ChallengeStatus.VERIFIED.value,
        device_id="device-001",
        attempts_used=1,
        max_attempts=3,
        dynamic_link_hash=None,
        challenge_expires_at=now,
        verified_at=now,
        created_at=now,
        updated_at=now
    )
    db_session.add(challenge)
    db_session.commit()
    
    # Test
    payload = {
        "profile_id": profile.id,
        "display_name": "K Evans Lettings",
        "nickname": None,
        "sort_code": "20-45-77",
        "account_number": "30019842",
        "payee_action_challenge_id": challenge.id,
        "payee_action_assertion": "123456"
    }
    
    response = auth_client.post("/api/v1/payees", json=payload)
    assert response.status_code == 200
    
    data = response.json()
    assert data["display_name"] == "K Evans Lettings"
    assert data["cop_result"] in ["match", "close_match", "no_match", "unavailable"]
    assert "can_proceed" in data
    assert "override_required" in data


def test_create_payee_without_sca(auth_client, db_session):
    """Test POST /api/v1/payees fails without verified SCA."""
    # Get the test user's profile (auth_client is logged in as admin@example.com -> "Admin User")
    profile = db_session.query(UserProfile).filter_by(display_name="Admin User").first()
    assert profile is not None
    
    # Test with non-existent challenge ID
    payload = {
        "profile_id": profile.id,
        "display_name": "Test Payee",
        "nickname": None,
        "sort_code": "12-34-56",
        "account_number": "12345678",
        "payee_action_challenge_id": 999999,
        "payee_action_assertion": "123456"
    }
    
    response = auth_client.post("/api/v1/payees", json=payload)
    assert response.status_code == 422


def test_confirm_cop_warning(auth_client, db_session):
    """Test POST /api/v1/payees/{id}/confirm-warning confirms override."""
    now = datetime.now(timezone.utc)
    
    # Get the test user's profile (auth_client is logged in as admin@example.com -> "Admin User")
    profile = db_session.query(UserProfile).filter_by(display_name="Admin User").first()
    assert profile is not None
    
    # Create payee with warning
    payee = Payee(
        profile_id=profile.id,
        display_name="Warning Payee",
        nickname=None,
        sort_code="99-99-99",
        account_number_last4="9999",
        account_number_hash="hash999",
        can_proceed=False,
        created_in_journey=True,
        payee_action_sca_verified_at=now,
        created_at=now,
        updated_at=now
    )
    db_session.add(payee)
    db_session.commit()
    
    # Create CoP result with warning
    cop = CoPResult(
        payee_id=payee.id,
        result_code=CoPResultCode.CLOSE_MATCH.value,
        decision_state=CoPDecisionState.PENDING.value,
        provider_reference="cop-ref-999",
        returned_name="Warning Payee Ltd",
        warning_message="Name is similar but not exact match",
        checked_at=now,
        override_confirmed_at=None,
        created_at=now,
        updated_at=now
    )
    db_session.add(cop)
    db_session.commit()
    
    # Test
    payload = {
        "override_reason": "Customer confirmed correct details"
    }
    
    response = auth_client.post(f"/api/v1/payees/{payee.id}/confirm-warning", json=payload)
    assert response.status_code == 200
    
    data = response.json()
    assert data["payee_id"] == payee.id
    assert data["can_proceed"] is True

"""Tests for payee service."""
from datetime import datetime, timezone
from app.services.payee_service import PayeeService
from app.models.profiles import UserProfile
from app.models.payees import Payee, CoPResult
from app.models.sca import StepUpChallenge
from app.models.auth import UserIdentity
from app.common.enums import (
    UserStatus, ProfileType, ChallengeType, ChallengeMethod,
    ChallengeStatus, CoPResultCode, CoPDecisionState
)


def test_get_payees(db_session):
    """Test getting payees for a profile."""
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
    
    # Create payee
    payee = Payee(
        profile_id=profile.id,
        display_name="Test Payee",
        nickname="Test",
        sort_code="12-34-56",
        account_number_last4="1234",
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
        returned_name="Test Payee",
        warning_message=None,
        checked_at=now,
        override_confirmed_at=None,
        created_at=now,
        updated_at=now
    )
    db_session.add(cop)
    db_session.commit()
    
    # Test
    service = PayeeService(db_session, "test-correlation-id")
    payees = service.get_payees(profile.id)
    
    assert len(payees) == 1
    assert payees[0]["payee_id"] == payee.id
    assert payees[0]["display_name"] == "Test Payee"
    assert payees[0]["latest_cop_result"] == CoPResultCode.MATCH.value
    assert payees[0]["can_proceed"] is True


def test_create_payee_with_sca(db_session):
    """Test creating a payee with SCA verification."""
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
    
    # Create verified SCA challenge
    from app.models.auth import AuthSession
    from app.common.enums import SessionState
    
    session = AuthSession(
        user_identity_id=user.id,
        token_hash="test-hash",
        session_state=SessionState.ACTIVE.value,
        issued_at=now,
        expires_at=now,
        last_activity_at=now,
        active_profile_id=profile.id,
        created_at=now,
        updated_at=now
    )
    db_session.add(session)
    db_session.commit()
    
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
    service = PayeeService(db_session, "test-correlation-id")
    result = service.create_payee(
        profile_id=profile.id,
        display_name="New Payee",
        nickname="New",
        sort_code="98-76-54",
        account_number="12345678",
        payee_action_challenge_id=challenge.id,
        payee_action_assertion="123456"
    )
    
    assert result["payee_id"] is not None
    assert result["display_name"] == "New Payee"
    assert result["cop_result"] in [CoPResultCode.MATCH.value, CoPResultCode.CLOSE_MATCH.value, 
                                     CoPResultCode.NO_MATCH.value, CoPResultCode.UNAVAILABLE.value]
    assert "can_proceed" in result
    assert "override_required" in result

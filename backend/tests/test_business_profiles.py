"""
Unit tests for business profile switching and entitlement checks.
Requirement: BR-ACCT-002, BR-ACCT-003, BR-ACCT-010 (Release 2)
Test Cases: TC-ACCT-018, TC-AUTH-017
"""
import uuid
from datetime import UTC, datetime
from unittest.mock import Mock

import pytest
from fastapi import HTTPException

from app.models.customer_profile_ref import CustomerProfileRef
from app.models.user_session import UserSession
from app.services.auth_service import AuthService


def test_switch_profile_success(db_session):
    """Test successful profile switching without re-authentication (TC-AUTH-017)."""
    customer_id = uuid.UUID("00000000-0000-0000-0000-000000000004")
    personal_profile_id = uuid.UUID("00000000-0000-0000-0000-000000000011")
    business_profile_id = uuid.UUID("00000000-0000-0000-0000-000000000012")
    
    # Create customer profiles
    personal_profile = CustomerProfileRef(
        id=personal_profile_id,
        customer_party_id="CUST-004",
        ciam_subject_reference="ciam-004",
        display_name="Alex Morgan",
        profile_type="personal",
        business_name=None,
        release_scope_status="in_scope",
        is_active=True
    )
    business_profile = CustomerProfileRef(
        id=business_profile_id,
        customer_party_id="CUST-004",
        ciam_subject_reference="ciam-004",
        display_name="SP Events Ltd",
        profile_type="business",
        business_name="SP Events Ltd",
        release_scope_status="in_scope",
        is_active=True
    )
    db_session.add(personal_profile)
    db_session.add(business_profile)
    
    # Create session with personal profile active
    session = UserSession(
        id=uuid.uuid4(),
        customer_profile_ref_id=personal_profile_id,
        active_profile_id=personal_profile_id,
        session_token_hash="test-token-hash",
        expires_at=datetime.now(UTC).replace(hour=23, minute=59, second=59),
        created_at=datetime.now(UTC),
        last_accessed_at=datetime.now(UTC)
    )
    db_session.add(session)
    db_session.commit()
    
    # Mock entitlement adapter to show business profile has entitlements
    entitlement_adapter = Mock()
    entitlement_adapter.get_profiles.return_value = [
        {
            "profile_id": str(personal_profile_id),
            "profile_type": "personal",
            "display_name": "Alex Morgan",
            "business_name": None,
            "has_entitlements": True
        },
        {
            "profile_id": str(business_profile_id),
            "profile_type": "business",
            "display_name": "SP Events Ltd",
            "business_name": "SP Events Ltd",
            "has_entitlements": True
        }
    ]
    
    # Create auth service
    auth_service = AuthService(
        db=db_session,
        entitlement_adapter=entitlement_adapter
    )
    
    # Execute profile switch
    result = auth_service.switch_profile(
        session_id=session.id,
        new_profile_id=business_profile_id
    )
    
    # Verify
    assert result["active_profile_id"] == str(business_profile_id)
    assert result["profile_type"] == "business"
    assert result["business_name"] == "SP Events Ltd"
    
    # Verify session updated
    db_session.refresh(session)
    assert session.active_profile_id == business_profile_id


def test_switch_profile_no_entitlements_denied(db_session):
    """Test profile switching denied when target profile has no entitlements (BR-ACCT-003)."""
    customer_id = uuid.UUID("00000000-0000-0000-0000-000000000004")
    personal_profile_id = uuid.UUID("00000000-0000-0000-0000-000000000011")
    business_profile_id = uuid.UUID("00000000-0000-0000-0000-000000000012")
    
    personal_profile = CustomerProfileRef(
        id=personal_profile_id,
        customer_party_id="CUST-004",
        ciam_subject_reference="ciam-004",
        display_name="Alex Morgan",
        profile_type="personal",
        business_name=None,
        release_scope_status="in_scope",
        is_active=True
    )
    business_profile = CustomerProfileRef(
        id=business_profile_id,
        customer_party_id="CUST-004",
        ciam_subject_reference="ciam-004",
        display_name="SP Events Ltd",
        profile_type="business",
        business_name="SP Events Ltd",
        release_scope_status="in_scope",
        is_active=True
    )
    db_session.add(personal_profile)
    db_session.add(business_profile)
    
    session = UserSession(
        id=uuid.uuid4(),
        customer_profile_ref_id=personal_profile_id,
        active_profile_id=personal_profile_id,
        session_token_hash="test-token-hash",
        expires_at=datetime.now(UTC).replace(hour=23, minute=59, second=59),
        created_at=datetime.now(UTC),
        last_accessed_at=datetime.now(UTC)
    )
    db_session.add(session)
    db_session.commit()
    
    # Mock entitlement adapter - business profile has NO entitlements
    entitlement_adapter = Mock()
    entitlement_adapter.get_profiles.return_value = [
        {
            "profile_id": str(personal_profile_id),
            "profile_type": "personal",
            "display_name": "Alex Morgan",
            "business_name": None,
            "has_entitlements": True
        },
        {
            "profile_id": str(business_profile_id),
            "profile_type": "business",
            "display_name": "SP Events Ltd",
            "business_name": "SP Events Ltd",
            "has_entitlements": False  # No entitlements
        }
    ]
    
    auth_service = AuthService(
        db=db_session,
        entitlement_adapter=entitlement_adapter
    )
    
    # Execute - should raise 403
    with pytest.raises(HTTPException) as exc_info:
        auth_service.switch_profile(
            session_id=session.id,
            new_profile_id=business_profile_id
        )
    
    assert exc_info.value.status_code == 403
    assert "no active entitlements" in exc_info.value.detail.lower()


def test_switch_profile_invalid_profile_id(db_session):
    """Test profile switching with non-existent profile ID."""
    personal_profile_id = uuid.UUID("00000000-0000-0000-0000-000000000011")
    invalid_profile_id = uuid.UUID("00000000-0000-0000-0000-999999999999")
    
    personal_profile = CustomerProfileRef(
        id=personal_profile_id,
        customer_party_id="CUST-004",
        ciam_subject_reference="ciam-004",
        display_name="Alex Morgan",
        profile_type="personal",
        business_name=None,
        release_scope_status="in_scope",
        is_active=True
    )
    db_session.add(personal_profile)
    
    session = UserSession(
        id=uuid.uuid4(),
        customer_profile_ref_id=personal_profile_id,
        active_profile_id=personal_profile_id,
        session_token_hash="test-token-hash",
        expires_at=datetime.now(UTC).replace(hour=23, minute=59, second=59),
        created_at=datetime.now(UTC),
        last_accessed_at=datetime.now(UTC)
    )
    db_session.add(session)
    db_session.commit()
    
    entitlement_adapter = Mock()
    entitlement_adapter.get_profiles.return_value = []
    
    auth_service = AuthService(
        db=db_session,
        entitlement_adapter=entitlement_adapter
    )
    
    # Execute - should raise 404
    with pytest.raises(HTTPException) as exc_info:
        auth_service.switch_profile(
            session_id=session.id,
            new_profile_id=invalid_profile_id
        )
    
    assert exc_info.value.status_code == 404
    assert "profile not found" in exc_info.value.detail.lower()


def test_get_available_profiles_filters_by_entitlements(db_session):
    """Test that available profiles list only includes profiles with entitlements (BRL-ACCT-03)."""
    customer_id = uuid.UUID("00000000-0000-0000-0000-000000000004")
    
    # Mock entitlement adapter
    entitlement_adapter = Mock()
    entitlement_adapter.get_profiles.return_value = [
        {
            "profile_id": "00000000-0000-0000-0000-000000000011",
            "profile_type": "personal",
            "display_name": "Alex Morgan",
            "business_name": None,
            "has_entitlements": True
        },
        {
            "profile_id": "00000000-0000-0000-0000-000000000012",
            "profile_type": "business",
            "display_name": "SP Events Ltd",
            "business_name": "SP Events Ltd",
            "has_entitlements": True
        },
        {
            "profile_id": "00000000-0000-0000-0000-000000000013",
            "profile_type": "business",
            "display_name": "Dormant Business",
            "business_name": "Dormant Business",
            "has_entitlements": False  # No entitlements - should be filtered out
        }
    ]
    
    auth_service = AuthService(
        db=db_session,
        entitlement_adapter=entitlement_adapter
    )
    
    # Get available profiles
    profiles = auth_service.get_available_profiles(customer_id)
    
    # Verify only profiles with entitlements are returned
    assert len(profiles) == 2
    assert profiles[0]["profile_id"] == "00000000-0000-0000-0000-000000000011"
    assert profiles[1]["profile_id"] == "00000000-0000-0000-0000-000000000012"
    assert all(p["has_entitlements"] for p in profiles)


def test_business_profile_display_includes_business_name(db_session):
    """Test business profile response includes business_name (TC-ACCT-018)."""
    business_profile_id = uuid.UUID("00000000-0000-0000-0000-000000000012")
    
    business_profile = CustomerProfileRef(
        id=business_profile_id,
        customer_party_id="CUST-004",
        ciam_subject_reference="ciam-004",
        display_name="SP Events Ltd",
        profile_type="business",
        business_name="SP Events Ltd",
        release_scope_status="in_scope",
        is_active=True
    )
    db_session.add(business_profile)
    db_session.commit()
    
    # Mock entitlement adapter
    entitlement_adapter = Mock()
    entitlement_adapter.get_profiles.return_value = [
        {
            "profile_id": str(business_profile_id),
            "profile_type": "business",
            "display_name": "SP Events Ltd",
            "business_name": "SP Events Ltd",
            "has_entitlements": True
        }
    ]
    
    auth_service = AuthService(
        db=db_session,
        entitlement_adapter=entitlement_adapter
    )
    
    # Get profile details
    profile = auth_service.get_profile_details(business_profile_id)
    
    # Verify business name is present
    assert profile["profile_type"] == "business"
    assert profile["business_name"] == "SP Events Ltd"
    assert profile["display_name"] == "SP Events Ltd"


def test_switch_profile_same_ciam_subject_required(db_session):
    """Test profile switching only allowed within same CIAM subject."""
    profile1_id = uuid.UUID("00000000-0000-0000-0000-000000000011")
    profile2_id = uuid.UUID("00000000-0000-0000-0000-000000000022")
    
    # Different CIAM subjects
    profile1 = CustomerProfileRef(
        id=profile1_id,
        customer_party_id="CUST-001",
        ciam_subject_reference="ciam-001",
        display_name="User One",
        profile_type="personal",
        business_name=None,
        release_scope_status="in_scope",
        is_active=True
    )
    profile2 = CustomerProfileRef(
        id=profile2_id,
        customer_party_id="CUST-002",
        ciam_subject_reference="ciam-002",  # Different CIAM subject
        display_name="User Two",
        profile_type="personal",
        business_name=None,
        release_scope_status="in_scope",
        is_active=True
    )
    db_session.add(profile1)
    db_session.add(profile2)
    
    session = UserSession(
        id=uuid.uuid4(),
        customer_profile_ref_id=profile1_id,
        active_profile_id=profile1_id,
        session_token_hash="test-token-hash",
        expires_at=datetime.now(UTC).replace(hour=23, minute=59, second=59),
        created_at=datetime.now(UTC),
        last_accessed_at=datetime.now(UTC)
    )
    db_session.add(session)
    db_session.commit()
    
    entitlement_adapter = Mock()
    entitlement_adapter.get_profiles.return_value = []
    
    auth_service = AuthService(
        db=db_session,
        entitlement_adapter=entitlement_adapter
    )
    
    # Execute - should raise 403 (different CIAM subject)
    with pytest.raises(HTTPException) as exc_info:
        auth_service.switch_profile(
            session_id=session.id,
            new_profile_id=profile2_id
        )
    
    assert exc_info.value.status_code == 403

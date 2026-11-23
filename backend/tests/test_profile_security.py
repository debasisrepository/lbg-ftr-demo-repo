"""
Security tests for profile switching (Release 2).
Requirement: SEC-004 remediation - prevent cross-identity profile switching
"""
import uuid

from app.models.customer_profile_ref import CustomerProfileRef
from app.models.sandbox_entitlement import SandboxEntitlement


def test_switch_profile_cross_identity_attack_blocked(auth_client, db_session):
    """
    SEC-004: Verify cross-identity profile switching is blocked.
    
    Attack scenario:
    1. User A authenticates with identity ciam-001
    2. User A attempts to switch to User B's profile (different identity ciam-002)
    3. Even if User B's profile has entitlements, the switch should be DENIED
    
    This test verifies the fix for SEC-004 Critical vulnerability.
    """
    # Get the authenticated user's identity
    current_customer = db_session.query(CustomerProfileRef).first()
    current_identity = current_customer.ciam_subject_reference
    
    # Create another customer profile with DIFFERENT identity
    other_customer_profile = CustomerProfileRef(
        id=uuid.uuid4(),
        customer_party_id="MALICIOUS-ATTACKER-TARGET",
        ciam_subject_reference="ciam-different-identity-999",  # DIFFERENT identity
        display_name="Victim User Profile",
        profile_type="business",
        business_name="Victim Business Ltd",
        release_scope_status="in_scope",
        is_active=True,
    )
    db_session.add(other_customer_profile)
    
    # Give the victim profile entitlements (attacker tries to exploit this)
    victim_entitlement = SandboxEntitlement(
        id=uuid.uuid4(),
        customer_profile_ref_id=other_customer_profile.id,
        resource_type="account",
        resource_reference="*",
        decision="allow",
        entitlement_type="view",
    )
    db_session.add(victim_entitlement)
    db_session.commit()
    
    # Attacker attempts to switch to victim's profile
    attack_response = auth_client.post("/api/v1/profiles/switch", json={
        "profile_id": str(other_customer_profile.id)
    })
    
    # CRITICAL SECURITY CHECK: Must be blocked
    assert attack_response.status_code == 404, (
        "SEC-004 CRITICAL: Cross-identity profile switching MUST return 404. "
        f"Got {attack_response.status_code}. "
        "An attacker should NOT be able to switch to profiles owned by different identities, "
        "even if those profiles have active entitlements."
    )
    
    # Verify error message doesn't leak information
    error_data = attack_response.json()
    assert "detail" in error_data
    # Should be generic message, not revealing the profile exists
    assert "not found" in error_data["detail"].lower() or "not accessible" in error_data["detail"].lower()


def test_switch_profile_same_identity_different_profiles_allowed(auth_client, db_session):
    """
    Verify that legitimate profile switching within the same identity DOES work.
    
    This is the positive test case to ensure SEC-004 fix doesn't break legitimate switching.
    """
    # Get the authenticated user's identity
    current_customer = db_session.query(CustomerProfileRef).first()
    current_identity = current_customer.ciam_subject_reference
    
    # Create another profile for the SAME identity (legitimate business profile)
    business_profile = CustomerProfileRef(
        id=uuid.uuid4(),
        customer_party_id="SAME-USER-BUSINESS",
        ciam_subject_reference=current_identity,  # SAME identity
        display_name="My Business Ltd",
        profile_type="business",
        business_name="My Business Ltd",
        release_scope_status="in_scope",
        is_active=True,
    )
    db_session.add(business_profile)
    
    # Give business profile entitlements
    business_entitlement = SandboxEntitlement(
        id=uuid.uuid4(),
        customer_profile_ref_id=business_profile.id,
        resource_type="account",
        resource_reference="*",
        decision="allow",
        entitlement_type="view",
    )
    db_session.add(business_entitlement)
    db_session.commit()
    
    # Legitimate switch to own business profile should succeed
    switch_response = auth_client.post("/api/v1/profiles/switch", json={
        "profile_id": str(business_profile.id)
    })
    
    assert switch_response.status_code == 200, (
        f"Legitimate profile switching should succeed. Got {switch_response.status_code}"
    )
    
    switch_data = switch_response.json()
    assert switch_data["active_profile_id"] == str(business_profile.id)
    assert switch_data["profile_type"] == "business"
    assert switch_data["business_name"] == "My Business Ltd"


def test_get_profiles_excludes_other_identities(auth_client, db_session):
    """
    SEC-004 related: Verify GET /profiles only returns profiles for the authenticated identity.
    """
    # Get the authenticated user's identity
    current_customer = db_session.query(CustomerProfileRef).first()
    current_identity = current_customer.ciam_subject_reference
    
    # Create profiles for different identities
    for i in range(3):
        other_profile = CustomerProfileRef(
            id=uuid.uuid4(),
            customer_party_id=f"OTHER-CUSTOMER-{i}",
            ciam_subject_reference=f"ciam-other-identity-{i}",  # Different identity
            display_name=f"Other User {i}",
            profile_type="personal",
            release_scope_status="in_scope",
            is_active=True,
        )
        db_session.add(other_profile)
        
        # Give them entitlements
        other_entitlement = SandboxEntitlement(
            id=uuid.uuid4(),
            customer_profile_ref_id=other_profile.id,
            resource_type="account",
            resource_reference="*",
            decision="allow",
            entitlement_type="view",
        )
        db_session.add(other_entitlement)
    
    db_session.commit()
    
    # Get profiles
    response = auth_client.get("/api/v1/profiles")
    assert response.status_code == 200
    
    data = response.json()
    profiles = data["profiles"]
    
    # Verify ALL returned profiles have the same CIAM identity
    for profile in profiles:
        profile_id = uuid.UUID(profile["profile_id"])
        profile_record = db_session.query(CustomerProfileRef).filter_by(id=profile_id).first()
        assert profile_record is not None
        assert profile_record.ciam_subject_reference == current_identity, (
            "GET /profiles returned a profile from a different identity - information disclosure vulnerability!"
        )

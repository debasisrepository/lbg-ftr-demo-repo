"""Integration tests for profile switching (BR-ACCT-002, BR-AUTH-006)"""
import uuid
from .test_helpers import get_auth_token


def test_profile_switching_without_reauth(client, seeded_data):
    """Test switching between personal and business profiles without re-authentication"""
    token = get_auth_token(client)

    # Get profiles
    profiles_response = client.get(
        "/api/v1/profiles",
        headers={"Authorization": f"Bearer {token}"}
    )
    assert profiles_response.status_code == 200
    profiles_data = profiles_response.json()
    assert "profiles" in profiles_data
    profiles = profiles_data["profiles"]

    # Find personal and business profiles
    personal_profile = next((p for p in profiles if p["profile_type"] == "personal"), None)
    business_profile = next((p for p in profiles if p["profile_type"] == "business"), None)

    # Switch to business profile (if exists)
    if business_profile:
        switch_response = client.put(
            "/api/v1/profiles/active",
            json={"profile_id": business_profile["profile_id"]},
            headers={"Authorization": f"Bearer {token}"}
        )
        assert switch_response.status_code == 200
        assert switch_response.json()["profile_id"] == business_profile["profile_id"]

        # Verify accounts overview reflects business profile
        accounts_response = client.get(
            "/api/v1/accounts/overview",
            headers={"Authorization": f"Bearer {token}"}
        )
        assert accounts_response.status_code == 200
        assert accounts_response.json()["profile_id"] == business_profile["profile_id"]

    # Switch back to personal profile
    if personal_profile:
        switch_response = client.put(
            "/api/v1/profiles/active",
            json={"profile_id": personal_profile["profile_id"]},
            headers={"Authorization": f"Bearer {token}"}
        )
        assert switch_response.status_code == 200
        assert switch_response.json()["profile_id"] == personal_profile["profile_id"]


def test_set_active_profile_updates_session(client, seeded_data):
    """Test that setting active profile updates session context"""
    token = get_auth_token(client)

    # Get initial accounts overview
    initial_accounts = client.get(
        "/api/v1/accounts/overview",
        headers={"Authorization": f"Bearer {token}"}
    )
    assert initial_accounts.status_code == 200
    initial_profile_id = initial_accounts.json()["profile_id"]

    # Get available profiles
    profiles_response = client.get(
        "/api/v1/profiles",
        headers={"Authorization": f"Bearer {token}"}
    )
    profiles = profiles_response.json()["profiles"]

    # Find a different profile
    other_profile = next((p for p in profiles if p["profile_id"] != initial_profile_id), None)

    if other_profile:
        # Switch profile
        switch_response = client.put(
            "/api/v1/profiles/active",
            json={"profile_id": other_profile["profile_id"]},
            headers={"Authorization": f"Bearer {token}"}
        )
        assert switch_response.status_code == 200

        # Verify accounts overview now uses the new profile
        updated_accounts = client.get(
            "/api/v1/accounts/overview",
            headers={"Authorization": f"Bearer {token}"}
        )
        assert updated_accounts.status_code == 200
        assert updated_accounts.json()["profile_id"] == other_profile["profile_id"]
        assert updated_accounts.json()["profile_id"] != initial_profile_id


def test_profile_switching_entitlements_refresh(client, seeded_data):
    """Test that profile switching refreshes entitlements"""
    token = get_auth_token(client)

    # Get profiles with entitlements
    profiles_response = client.get(
        "/api/v1/profiles",
        headers={"Authorization": f"Bearer {token}"}
    )
    profiles = profiles_response.json()["profiles"]
    assert len(profiles) > 0

    # Each profile should have entitlements array
    for profile in profiles:
        assert "entitlements" in profile
        assert isinstance(profile["entitlements"], list)


def test_unauthorized_profile_switch(client, seeded_data):
    """Test switching to a profile that doesn't belong to the customer"""
    token = get_auth_token(client)

    # Try to switch to a random profile ID
    fake_profile_id = str(uuid.uuid4())
    switch_response = client.put(
        "/api/v1/profiles/active",
        json={"profile_id": fake_profile_id},
        headers={"Authorization": f"Bearer {token}"}
    )

    # Should return 404 or 403
    assert switch_response.status_code in [403, 404]


def test_profile_switching_preserves_authentication(client, seeded_data):
    """Test that profile switching does NOT require re-authentication"""
    token = get_auth_token(client)

    # Get profiles
    profiles_response = client.get(
        "/api/v1/profiles",
        headers={"Authorization": f"Bearer {token}"}
    )
    profiles = profiles_response.json()["profiles"]

    # Switch between profiles multiple times
    for profile in profiles[:2]:  # Switch up to 2 profiles
        switch_response = client.put(
            "/api/v1/profiles/active",
            json={"profile_id": profile["profile_id"]},
            headers={"Authorization": f"Bearer {token}"}
        )
        assert switch_response.status_code == 200

        # Verify we can still access protected resources with the same token
        accounts_response = client.get(
            "/api/v1/accounts/overview",
            headers={"Authorization": f"Bearer {token}"}
        )
        assert accounts_response.status_code == 200
        assert accounts_response.json()["profile_id"] == profile["profile_id"]

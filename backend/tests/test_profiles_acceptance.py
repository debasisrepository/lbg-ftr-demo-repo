"""Acceptance tests for profiles endpoints"""


def test_get_profiles_requires_auth(client):
    """Test GET /api/v1/profiles requires authentication"""
    response = client.get("/api/v1/profiles")
    assert response.status_code in (401, 403)  # Either unauthorized or forbidden


def test_get_profiles_returns_list(auth_client, db_session):
    """Test GET /api/v1/profiles returns profiles"""
    response = auth_client.get("/api/v1/profiles")
    assert response.status_code == 200
    data = response.json()
    assert "profiles" in data
    assert isinstance(data["profiles"], list)


def test_set_active_profile(auth_client, db_session):
    """Test PUT /api/v1/profiles/active sets active profile"""
    # Get profiles first
    response = auth_client.get("/api/v1/profiles")
    assert response.status_code == 200
    profiles = response.json()["profiles"]

    if profiles:
        profile_id = profiles[0]["profile_id"]

        # Set active profile
        response = auth_client.put(
            "/api/v1/profiles/active",
            json={"profile_id": profile_id}
        )
        assert response.status_code == 200
        data = response.json()
        assert data["profile_id"] == profile_id
        assert "display_name" in data

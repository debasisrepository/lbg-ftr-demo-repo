"""Smoke tests."""


def test_login_smoke(auth_client):
    """Test login through helper."""
    session_id = getattr(auth_client, "_session_id", None)
    assert session_id is not None, "session_id not set on auth_client"
    response = auth_client.get(f"/api/v1/auth/me?session_id={session_id}")
    assert response.status_code == 200
    data = response.json()
    assert "user" in data
    assert data["user"]["username"] == "tester@example.com"


def test_health_check(client):
    """Test health endpoint."""
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json() == {"status": "ok"}


def test_health_ready(client):
    """Test readiness check."""
    response = client.get("/health/ready")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "ready"
    assert data["database"] == "connected"

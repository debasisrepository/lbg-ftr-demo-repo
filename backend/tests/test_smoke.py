"""Smoke test for basic application functionality."""


def test_health_endpoint(client):
    """Test health endpoint returns OK."""
    response = client.get("/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "ok"
    assert "service" in data
    assert "version" in data


def test_api_health_endpoint(client):
    """Test API health endpoint returns OK."""
    response = client.get("/api/v1/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "ok"


def test_models_import():
    """Test that models import successfully."""
    from app.models.users import User
    from app.core.security import verify_password, hash_password
    
    # Test password hashing
    password = "test123"
    hashed = hash_password(password)
    assert verify_password(password, hashed)
    assert not verify_password("wrong", hashed)
    
    print("OK")

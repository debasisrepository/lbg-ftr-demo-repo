"""Smoke tests for backend API"""


def test_health_check(client):
    """Test health check endpoint"""
    response = client.get("/api/v1/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "ok"


def test_readiness_check(client):
    """Test readiness check endpoint"""
    response = client.get("/api/v1/health/ready")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "ready"
    assert "capabilities" in data
    assert isinstance(data["capabilities"], list)
    # Check that capabilities array contains expected items
    capability_names = [cap["name"] for cap in data["capabilities"]]
    assert "database" in capability_names
    assert "payments" in capability_names


def test_root_endpoint(client):
    """Test root endpoint"""
    response = client.get("/")
    assert response.status_code == 200
    data = response.json()
    assert data["service"] == "Sample Bank Mobile Payments MVP"
    assert data["status"] == "running"


def test_database_models_load(db_session):
    """Test that all models are registered and importable"""
    from app.models import AuditEvent, BankAccount, Customer, Entitlement, PaymentOrder, Profile, RefCode, Session
    # If imports work, models are registered
    assert RefCode is not None
    assert Customer is not None
    assert Profile is not None
    assert Entitlement is not None
    assert BankAccount is not None
    assert Session is not None
    assert PaymentOrder is not None
    assert AuditEvent is not None

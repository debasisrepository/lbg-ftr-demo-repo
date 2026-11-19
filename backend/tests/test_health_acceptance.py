"""Health router acceptance tests"""


def test_health_check(client):
    """Test basic health check"""
    response = client.get("/api/v1/health")

    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "ok"


def test_readiness_check(client):
    """Test readiness check with capabilities"""
    response = client.get("/api/v1/health/ready")

    assert response.status_code == 200
    data = response.json()
    assert "status" in data
    assert "capabilities" in data
    assert isinstance(data["capabilities"], list)

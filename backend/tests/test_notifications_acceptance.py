"""Notifications router acceptance tests"""


def test_list_notifications(client):
    """Test listing customer notifications"""
    response = client.get("/api/v1/notifications")

    assert response.status_code == 200
    data = response.json()
    assert "items" in data
    assert "total" in data
    assert "unread_count" in data
    assert isinstance(data["items"], list)


def test_get_service_status(client):
    """Test retrieving service status notices"""
    response = client.get("/api/v1/notifications/service-status")

    assert response.status_code == 200
    data = response.json()
    assert "items" in data
    assert "total" in data
    assert isinstance(data["items"], list)

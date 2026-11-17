def test_smoke_login(auth_client):
    response = auth_client.get("/api/v1/auth/me")
    assert response.status_code == 200
    data = response.json()
    assert data["email"] == "tester@example.com"
    assert data["is_active"] is True

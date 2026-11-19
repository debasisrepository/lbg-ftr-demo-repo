"""Acceptance tests for payees endpoints"""


def test_get_payees_requires_auth(client):
    """Test GET /api/v1/payees requires authentication"""
    response = client.get("/api/v1/payees")
    assert response.status_code in (401, 403)  # Either unauthorized or forbidden


def test_get_payees(auth_client, db_session):
    """Test GET /api/v1/payees returns payees"""
    response = auth_client.get("/api/v1/payees")
    assert response.status_code == 200
    data = response.json()
    assert "payees" in data
    assert isinstance(data["payees"], list)


def test_create_payee(auth_client, db_session):
    """Test POST /api/v1/payees creates payee with CoP check"""
    response = auth_client.post(
        "/api/v1/payees",
        json={
            "payee_name": "Test Payee",
            "sort_code": "12-34-56",
            "account_number": "12345678",
            "payee_type": "personal"
        }
    )
    assert response.status_code == 200
    data = response.json()

    assert "payee" in data
    assert "cop_check" in data
    assert data["payee"]["payee_name"] == "Test Payee"
    assert data["payee"]["account_number_masked"] == "****5678"
    assert data["cop_check"]["outcome"] in ["match", "partial_match", "mismatch", "unavailable"]


def test_get_payee_by_id(auth_client, db_session):
    """Test GET /api/v1/payees/{id} returns specific payee"""
    # Create a payee first
    create_response = auth_client.post(
        "/api/v1/payees",
        json={
            "payee_name": "Test Payee 2",
            "sort_code": "98-76-54",
            "account_number": "87654321",
            "payee_type": "personal"
        }
    )
    assert create_response.status_code == 200
    payee_id = create_response.json()["payee"]["payee_id"]

    # Get the payee
    response = auth_client.get(f"/api/v1/payees/{payee_id}")
    assert response.status_code == 200
    data = response.json()
    assert data["payee_id"] == payee_id
    assert data["payee_name"] == "Test Payee 2"


def test_update_payee(auth_client, db_session):
    """Test PUT /api/v1/payees/{id} updates payee"""
    # Create a payee first
    create_response = auth_client.post(
        "/api/v1/payees",
        json={
            "payee_name": "Original Name",
            "sort_code": "12-34-56",
            "account_number": "12345678",
            "payee_type": "personal"
        }
    )
    assert create_response.status_code == 200
    payee_id = create_response.json()["payee"]["payee_id"]

    # Update the payee
    response = auth_client.put(
        f"/api/v1/payees/{payee_id}",
        json={"payee_name": "Updated Name"}
    )
    assert response.status_code == 200
    data = response.json()
    assert data["payee"]["payee_name"] == "Updated Name"

    # CoP check should be triggered on update
    if data["cop_check"]:
        assert "outcome" in data["cop_check"]


def test_acknowledge_cop(auth_client, db_session):
    """Test POST /api/v1/payees/{id}/cop-acknowledgement"""
    # Create a payee
    create_response = auth_client.post(
        "/api/v1/payees",
        json={
            "payee_name": "Test Payee 3",
            "sort_code": "11-22-33",
            "account_number": "11223344",
            "payee_type": "personal"
        }
    )
    assert create_response.status_code == 200
    payee_id = create_response.json()["payee"]["payee_id"]

    # Acknowledge CoP result
    response = auth_client.post(
        f"/api/v1/payees/{payee_id}/cop-acknowledgement",
        json={"acknowledged": True}
    )
    assert response.status_code == 200
    data = response.json()
    assert data["payee_id"] == payee_id
    assert "acknowledged_at" in data


def test_run_cop_check(auth_client, db_session):
    """Test POST /api/v1/payees/{id}/cop-checks runs manual CoP check"""
    # Create a payee
    create_response = auth_client.post(
        "/api/v1/payees",
        json={
            "payee_name": "Test Payee 4",
            "sort_code": "44-55-66",
            "account_number": "44556677",
            "payee_type": "personal"
        }
    )
    assert create_response.status_code == 200
    payee_id = create_response.json()["payee"]["payee_id"]

    # Run manual CoP check
    response = auth_client.post(
        f"/api/v1/payees/{payee_id}/cop-checks",
        json={"reason": "recheck"}
    )
    assert response.status_code == 200
    data = response.json()
    assert "cop_check" in data
    assert data["cop_check"]["outcome"] in ["match", "partial_match", "mismatch", "unavailable"]

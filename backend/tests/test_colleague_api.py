"""Test colleague API endpoints."""
import uuid


def test_list_colleague_cases_requires_colleague_role(auth_client):
    """Test colleague worklist requires colleague role."""
    # auth_client is logged in as admin@example.com (not colleague)
    response = auth_client.get("/api/v1/colleague/cases")
    assert response.status_code == 403


def test_colleague_login(client, db_session):
    """Test colleague can log in."""
    from app.auth.models import AppUser
    from app.auth.passwords import PasswordHasher
    
    # Seed colleague user
    db_session.add(AppUser(
        email="colleague@example.com",
        hashed_password=PasswordHasher.hash_password("colleague123"),
        is_active=True,
        is_colleague=True,
        customer_reference=None,
        brand=None,
        failed_login_count=0
    ))
    db_session.commit()
    
    response = client.post(
        "/api/v1/auth/login",
        json={"email": "colleague@example.com", "password": "colleague123"}
    )
    assert response.status_code == 200
    data = response.json()
    assert data["access_token"]
    assert "colleague" in data["email"]


def test_colleague_list_cases(client, db_session):
    """Test colleague can list cases."""
    from app.auth.models import AppUser
    from app.auth.passwords import PasswordHasher
    
    # Seed colleague user
    db_session.add(AppUser(
        email="colleague@example.com",
        hashed_password=PasswordHasher.hash_password("colleague123"),
        is_active=True,
        is_colleague=True,
        customer_reference=None,
        brand=None,
        failed_login_count=0
    ))
    db_session.commit()
    
    # Login as colleague
    login_resp = client.post(
        "/api/v1/auth/login",
        json={"email": "colleague@example.com", "password": "colleague123"}
    )
    assert login_resp.status_code == 200
    token = login_resp.json()["access_token"]
    
    # List cases
    client.headers["Authorization"] = f"Bearer {token}"
    response = client.get("/api/v1/colleague/cases")
    
    assert response.status_code == 200
    data = response.json()
    assert "items" in data
    assert "total" in data
    assert isinstance(data["items"], list)


def test_colleague_create_case(client, db_session):
    """Test colleague can create case from desktop."""
    from app.auth.models import AppUser
    from app.auth.passwords import PasswordHasher
    
    # Seed colleague user
    db_session.add(AppUser(
        email="colleague@example.com",
        hashed_password=PasswordHasher.hash_password("colleague123"),
        is_active=True,
        is_colleague=True,
        customer_reference=None,
        brand=None,
        failed_login_count=0
    ))
    db_session.commit()
    
    # Login as colleague
    login_resp = client.post(
        "/api/v1/auth/login",
        json={"email": "colleague@example.com", "password": "colleague123"}
    )
    token = login_resp.json()["access_token"]
    
    # Create case
    client.headers["Authorization"] = f"Bearer {token}"
    response = client.post(
        "/api/v1/colleague/cases",
        json={
            "origin_source": "colleague_desktop",
            "problem_statement": "Customer called about card issue"
        }
    )
    
    assert response.status_code == 200
    data = response.json()
    assert data["case_ref"]
    assert "CP-" in data["case_ref"]

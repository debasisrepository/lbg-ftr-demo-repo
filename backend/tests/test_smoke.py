"""
Smoke tests for basic application functionality.
"""


def test_health_check(client):
    """Test the health check endpoint."""
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json() == {"status": "ok"}


def test_readiness_check(client):
    """Test the readiness check endpoint."""
    response = client.get("/health/ready")
    assert response.status_code == 200
    assert response.json() == {"status": "ok"}


def test_database_connection(db_session):
    """Test that database connection works."""
    from app.models.customer_profile_ref import CustomerProfileRef
    
    # Query should not raise an exception
    customers = db_session.query(CustomerProfileRef).all()
    assert isinstance(customers, list)


def test_test_customer_fixture(test_customer, db_session):
    """Test that the test_customer fixture creates a valid customer."""
    from app.models.customer_profile_ref import CustomerProfileRef
    
    customer_id = test_customer["customer"].id
    customer = db_session.query(CustomerProfileRef).filter_by(id=customer_id).first()
    
    assert customer is not None
    assert customer.display_name == "Test User"
    assert customer.is_active is True
    assert test_customer["passcode"] == "Test1234"

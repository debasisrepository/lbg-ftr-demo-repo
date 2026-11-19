"""Acceptance tests for accounts endpoints"""


def test_get_accounts_overview_requires_auth(client):
    """Test GET /api/v1/accounts/overview requires authentication"""
    response = client.get("/api/v1/accounts/overview")
    assert response.status_code in (401, 403)  # Either unauthorized or forbidden


def test_get_accounts_overview(auth_client, db_session):
    """Test GET /api/v1/accounts/overview returns accounts and loans"""
    response = auth_client.get("/api/v1/accounts/overview")
    assert response.status_code == 200
    data = response.json()

    assert "accounts" in data
    assert "loans" in data
    assert "profile_id" in data
    assert "profile_display_name" in data
    assert isinstance(data["accounts"], list)
    assert isinstance(data["loans"], list)


def test_accounts_have_required_fields(auth_client, db_session):
    """Test account objects have required fields"""
    response = auth_client.get("/api/v1/accounts/overview")
    assert response.status_code == 200
    data = response.json()

    if data["accounts"]:
        account = data["accounts"][0]
        assert "bank_account_id" in account
        assert "account_type" in account
        assert "account_name" in account
        assert "currency_code" in account
        assert "source_status" in account
        assert "payment_permission" in account


def test_loans_have_required_fields(auth_client, db_session):
    """Test loan objects have required fields"""
    response = auth_client.get("/api/v1/accounts/overview")
    assert response.status_code == 200
    data = response.json()

    if data["loans"]:
        loan = data["loans"][0]
        assert "loan_snapshot_id" in loan
        assert "loan_name" in loan
        assert "currency_code" in loan
        assert "source_status" in loan

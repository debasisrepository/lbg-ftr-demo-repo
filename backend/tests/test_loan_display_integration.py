"""Integration tests for loan view display (BR-ACCT-004)"""
from .test_helpers import get_auth_token


def test_accounts_overview_includes_loans(client, seeded_data):
    """Test GET /api/v1/accounts/overview returns loans with repayment info"""
    token = get_auth_token(client)

    # Get accounts overview
    response = client.get(
        "/api/v1/accounts/overview",
        headers={"Authorization": f"Bearer {token}"}
    )

    assert response.status_code == 200
    data = response.json()
    assert "accounts" in data
    assert "loans" in data
    assert isinstance(data["loans"], list)


def test_loan_next_repayment_fields_present(client, seeded_data):
    """Test that loan objects include next_repayment_minor and next_repayment_date"""
    token = get_auth_token(client)

    # Get accounts overview
    response = client.get(
        "/api/v1/accounts/overview",
        headers={"Authorization": f"Bearer {token}"}
    )

    data = response.json()
    loans = data["loans"]

    # If loans exist, verify they have repayment fields
    for loan in loans:
        assert "loan_snapshot_id" in loan
        assert "loan_name" in loan
        assert "outstanding_balance_minor" in loan
        assert "next_repayment_minor" in loan
        assert "next_repayment_date" in loan
        assert "currency_code" in loan
        assert "source_status" in loan


def test_loan_outstanding_balance_visible(client, seeded_data):
    """Test that loans show outstanding balance"""
    token = get_auth_token(client)

    # Get accounts overview
    response = client.get(
        "/api/v1/accounts/overview",
        headers={"Authorization": f"Bearer {token}"}
    )

    data = response.json()
    loans = data["loans"]

    for loan in loans:
        # Outstanding balance should be present (can be None for unavailable)
        assert "outstanding_balance_minor" in loan
        if loan["source_status"] == "fresh":
            # Fresh data should have a balance
            assert loan["outstanding_balance_minor"] is not None


def test_loan_with_missing_data_graceful_degradation(client, seeded_data):
    """Test that missing loan data is handled gracefully (null fields allowed)"""
    token = get_auth_token(client)

    # Get accounts overview
    response = client.get(
        "/api/v1/accounts/overview",
        headers={"Authorization": f"Bearer {token}"}
    )

    assert response.status_code == 200
    data = response.json()

    # Loans array should exist even if empty
    assert "loans" in data
    loans = data["loans"]

    # Each loan should have nullable fields without causing errors
    for loan in loans:
        # These fields can be None
        _ = loan.get("next_repayment_minor")
        _ = loan.get("next_repayment_date")
        _ = loan.get("outstanding_balance_minor")

        # Source status indicates data availability
        assert loan["source_status"] in ["fresh", "stale", "unavailable"]


def test_loan_freshness_indicator(client, seeded_data):
    """Test that loans include freshness_at and source_status fields"""
    token = get_auth_token(client)

    # Get accounts overview
    response = client.get(
        "/api/v1/accounts/overview",
        headers={"Authorization": f"Bearer {token}"}
    )

    data = response.json()
    loans = data["loans"]

    for loan in loans:
        # Verify freshness indicators present
        assert "freshness_at" in loan
        assert "source_status" in loan

        # If stale or unavailable, freshness_at may be old or None
        if loan["source_status"] == "unavailable":
            # Unavailable loans might not have data
            pass
        elif loan["source_status"] == "fresh":
            # Fresh loans should have recent freshness_at
            assert loan["freshness_at"] is not None

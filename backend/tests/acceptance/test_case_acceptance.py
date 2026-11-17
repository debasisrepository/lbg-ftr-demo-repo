"""Acceptance tests for case API endpoints."""
import pytest


def test_post_cases_creates_new_case(auth_client):
    """Test POST /api/v1/cases creates a new case."""
    # Execute
    response = auth_client.post(
        "/api/v1/cases",
        json={
            "issue_type": "card_declined",
            "issue_summary": "My card was declined at the grocery store",
            "origin_channel": "mobile_app"
        }
    )
    
    # Assert
    assert response.status_code == 201
    data = response.json()
    assert data["outcome"] == "created"
    assert data["case"] is not None
    assert data["case"]["case_reference"].startswith("CP-")
    assert data["case"]["issue_type"] == "card_declined"
    assert data["case"]["current_lifecycle_state"] == "case_created"
    assert data["case"]["status_code"] == "received"
    assert data["classification_source"] == "eligibility_rule"
    assert data["anchor_reference"] is not None
    assert data["case"]["owner"]["owner_team_code"] == "INTAKE_DEFAULT"
    assert data["case"]["expected_by"]["commitment_state"] == "under_review"


def test_post_cases_surfaces_existing_open_case(auth_client):
    """Test POST /api/v1/cases surfaces existing open case instead of creating duplicate."""
    # Create first case
    first_response = auth_client.post(
        "/api/v1/cases",
        json={
            "issue_type": "payment_missing",
            "issue_summary": "Payment not received",
            "origin_channel": "mobile_app"
        }
    )
    assert first_response.status_code == 201
    first_data = first_response.json()
    first_reference = first_data["case"]["case_reference"]
    
    # Try to create another case with same issue_type
    second_response = auth_client.post(
        "/api/v1/cases",
        json={
            "issue_type": "payment_missing",
            "issue_summary": "Still missing payment",
            "origin_channel": "web"
        }
    )
    
    # Assert - should surface, not create
    assert second_response.status_code == 200
    second_data = second_response.json()
    assert second_data["outcome"] == "surfaced"
    assert second_data["case"]["case_reference"] == first_reference
    assert second_data["classification_source"] == "eligibility_rule"


def test_post_cases_returns_not_eligible_for_ineligible_issue(auth_client):
    """Test POST /api/v1/cases returns not_eligible for ineligible issue types."""
    # Execute
    response = auth_client.post(
        "/api/v1/cases",
        json={
            "issue_type": "general_query",
            "issue_summary": "Just a general question",
            "origin_channel": "mobile_app"
        }
    )
    
    # Assert
    assert response.status_code == 200
    data = response.json()
    assert data["outcome"] == "not_eligible"
    assert data["case"] is None
    assert data["redirect_journey_code"] == "existing_support"
    assert "redirect_message" in data


def test_post_cases_rejects_restricted_data(auth_client):
    """Test POST /api/v1/cases rejects requests with restricted data."""
    # Execute - include PAN in summary (using valid Luhn test card)
    response = auth_client.post(
        "/api/v1/cases",
        json={
            "issue_type": "card_declined",
            "issue_summary": "My card 4111111111111111 was declined",
            "origin_channel": "mobile_app"
        }
    )
    
    # Assert
    assert response.status_code == 422
    data = response.json()
    assert "restricted data" in data["detail"][0]["msg"].lower()


def test_post_cases_requires_authentication(client):
    """Test POST /api/v1/cases requires authentication."""
    # Execute without auth
    response = client.post(
        "/api/v1/cases",
        json={
            "issue_type": "card_declined",
            "issue_summary": "My card was declined",
            "origin_channel": "mobile_app"
        }
    )
    
    # Assert
    assert response.status_code == 401


def test_get_cases_by_reference_returns_case_detail(auth_client):
    """Test GET /api/v1/cases/{reference} returns case detail."""
    # Setup - create a case first
    create_response = auth_client.post(
        "/api/v1/cases",
        json={
            "issue_type": "card_declined",
            "issue_summary": "Card declined at store",
            "origin_channel": "mobile_app"
        }
    )
    assert create_response.status_code == 201
    case_reference = create_response.json()["case"]["case_reference"]
    
    # Execute
    response = auth_client.get(f"/api/v1/cases/{case_reference}")
    
    # Assert
    assert response.status_code == 200
    data = response.json()
    assert data["case_reference"] == case_reference
    assert data["issue_type"] == "card_declined"
    assert data["current_lifecycle_state"] == "case_created"
    assert data["status_code"] == "received"
    assert "owner" in data
    assert "expected_by" in data
    assert data["owner"]["owner_team_code"] == "INTAKE_DEFAULT"
    assert data["expected_by"]["commitment_state"] == "under_review"


def test_get_cases_by_reference_returns_404_for_nonexistent(auth_client):
    """Test GET /api/v1/cases/{reference} returns 404 for nonexistent case."""
    # Execute
    response = auth_client.get("/api/v1/cases/CP-NONEXISTENT")
    
    # Assert
    assert response.status_code == 404


def test_get_cases_by_reference_returns_404_for_other_customer(auth_client, client):
    """Test GET /api/v1/cases/{reference} returns 404 for another customer's case."""
    # Setup - create case as auth_client user
    create_response = auth_client.post(
        "/api/v1/cases",
        json={
            "issue_type": "card_declined",
            "issue_summary": "My card declined",
            "origin_channel": "mobile_app"
        }
    )
    assert create_response.status_code == 201
    case_reference = create_response.json()["case"]["case_reference"]
    
    # Login as different user
    login_response = client.post(
        "/api/v1/auth/login",
        json={"username": "user1@example.com", "password": "user123"}
    )
    assert login_response.status_code == 200
    other_token = login_response.json()["access_token"]
    
    # Execute - try to get case as different user
    response = client.get(
        f"/api/v1/cases/{case_reference}",
        headers={"Authorization": f"Bearer {other_token}"}
    )
    
    # Assert
    assert response.status_code == 404


def test_get_cases_by_reference_requires_authentication(client):
    """Test GET /api/v1/cases/{reference} requires authentication."""
    # Execute without auth
    response = client.get("/api/v1/cases/CP-TEST123")
    
    # Assert
    assert response.status_code == 401

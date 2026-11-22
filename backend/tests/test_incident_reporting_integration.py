"""Integration tests for incident reporting (BR-OPS-008)"""
import uuid

import pytest
from .test_helpers import get_auth_token


def test_create_incident_report_success(client, seeded_data):
    """Test POST /api/v1/incidents with valid data"""
    token = get_auth_token(client)

    # Create incident report
    response = client.post(
        "/api/v1/incidents",
        json={
            "incident_category": "technical_issue",
            "incident_title": "Mobile app crashes on login",
            "incident_description": "The app crashes immediately after entering credentials",
            "severity": "high"
        },
        headers={"Authorization": f"Bearer {token}"}
    )

    assert response.status_code == 201
    data = response.json()
    assert data["incident_category"] == "technical_issue"
    assert data["incident_title"] == "Mobile app crashes on login"
    assert data["severity"] == "high"
    assert data["status"] in ["reported", "acknowledged"]
    assert data["incident_reference"] is not None
    assert data["incident_reference"].startswith("INC")
    assert data["external_incident_ref"] is not None


def test_create_incident_report_all_categories(client, seeded_data):
    """Test creating incident reports with all valid categories"""
    token = get_auth_token(client)

    valid_categories = ['technical_issue', 'service_outage', 'data_issue', 'security_concern', 'other']

    for category in valid_categories:
        response = client.post(
            "/api/v1/incidents",
            json={
                "incident_category": category,
                "incident_title": f"Test {category}",
                "incident_description": "Test description",
                "severity": "medium"
            },
            headers={"Authorization": f"Bearer {token}"}
        )
        assert response.status_code == 201
        assert response.json()["incident_category"] == category


def test_create_incident_report_invalid_category(client, seeded_data):
    """Test creating incident report with invalid category"""
    token = get_auth_token(client)

    response = client.post(
        "/api/v1/incidents",
        json={
            "incident_category": "invalid_category",
            "incident_title": "Test",
            "incident_description": "Test",
            "severity": "medium"
        },
        headers={"Authorization": f"Bearer {token}"}
    )

    assert response.status_code == 400
    assert "Invalid incident category" in response.json()["detail"]


def test_create_incident_report_unauthorized(client, seeded_data):
    """Test creating incident report without authentication"""
    response = client.post(
        "/api/v1/incidents",
        json={
            "incident_category": "technical_issue",
            "incident_title": "Test",
            "incident_description": "Test",
            "severity": "medium"
        }
    )

    assert response.status_code in [401, 403]


def test_get_incident_report(client, seeded_data):
    """Test GET /api/v1/incidents/{reference}"""
    token = get_auth_token(client)

    # Create incident
    create_response = client.post(
        "/api/v1/incidents",
        json={
            "incident_category": "technical_issue",
            "incident_title": "Test incident",
            "incident_description": "Test description",
            "severity": "low"
        },
        headers={"Authorization": f"Bearer {token}"}
    )
    assert create_response.status_code == 201
    incident_reference = create_response.json()["incident_reference"]

    # Get incident by reference
    get_response = client.get(
        f"/api/v1/incidents/{incident_reference}",
        headers={"Authorization": f"Bearer {token}"}
    )
    assert get_response.status_code == 200
    data = get_response.json()
    assert data["incident_reference"] == incident_reference
    assert data["incident_title"] == "Test incident"


def test_list_customer_incidents(client, seeded_data):
    """Test GET /api/v1/incidents returns customer's incidents"""
    token = get_auth_token(client)

    # Create multiple incidents
    for i in range(3):
        client.post(
            "/api/v1/incidents",
            json={
                "incident_category": "technical_issue",
                "incident_title": f"Test incident {i}",
                "incident_description": f"Description {i}",
                "severity": "low"
            },
            headers={"Authorization": f"Bearer {token}"}
        )

    # List incidents
    list_response = client.get(
        "/api/v1/incidents",
        headers={"Authorization": f"Bearer {token}"}
    )
    assert list_response.status_code == 200
    incidents = list_response.json()
    assert len(incidents) >= 3
    assert all(inc["incident_title"].startswith("Test incident") for inc in incidents[:3])

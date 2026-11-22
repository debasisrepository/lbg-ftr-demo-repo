"""Acceptance tests for incident reporting API (BR-OPS-008)"""
import uuid

import pytest


def test_create_incident_report_authenticated(auth_client):
    """Test creating incident report as authenticated user"""
    response = auth_client.post(
        "/api/v1/incidents",
        json={
            "incident_category": "technical_issue",
            "incident_title": "Cannot load payment page",
            "incident_description": "The payment page shows a blank screen",
            "severity": "high"
        }
    )

    assert response.status_code == 201
    data = response.json()
    assert "incident_report_id" in data
    assert data["incident_category"] == "technical_issue"
    assert data["incident_title"] == "Cannot load payment page"
    assert data["severity"] == "high"
    assert data["status"] in ["reported", "acknowledged"]
    assert data["incident_reference"] is not None
    assert data["incident_reference"].startswith("INC")


def test_create_incident_report_unauthenticated(client):
    """Test creating incident report without authentication fails"""
    response = client.post(
        "/api/v1/incidents",
        json={
            "incident_category": "technical_issue",
            "incident_title": "Test",
            "incident_description": "Test",
            "severity": "low"
        }
    )

    assert response.status_code == 403


def test_create_incident_report_invalid_category(auth_client):
    """Test creating incident report with invalid category"""
    response = auth_client.post(
        "/api/v1/incidents",
        json={
            "incident_category": "invalid_category",
            "incident_title": "Test",
            "incident_description": "Test",
            "severity": "low"
        }
    )

    assert response.status_code == 400
    assert "Invalid incident category" in response.json()["detail"]


def test_create_incident_report_invalid_severity(auth_client):
    """Test creating incident report with invalid severity"""
    response = auth_client.post(
        "/api/v1/incidents",
        json={
            "incident_category": "technical_issue",
            "incident_title": "Test",
            "incident_description": "Test",
            "severity": "extreme"
        }
    )

    assert response.status_code == 400
    assert "Invalid severity" in response.json()["detail"]


def test_get_incident_report_by_reference(auth_client):
    """Test retrieving incident report by reference"""
    # Create incident
    create_response = auth_client.post(
        "/api/v1/incidents",
        json={
            "incident_category": "data_issue",
            "incident_title": "Missing balance",
            "incident_description": "Account balance not displaying",
            "severity": "medium"
        }
    )
    incident_reference = create_response.json()["incident_reference"]

    # Retrieve incident
    get_response = auth_client.get(f"/api/v1/incidents/{incident_reference}")

    assert get_response.status_code == 200
    data = get_response.json()
    assert data["incident_reference"] == incident_reference
    assert data["incident_title"] == "Missing balance"


def test_get_incident_report_not_found(auth_client):
    """Test retrieving non-existent incident report"""
    response = auth_client.get("/api/v1/incidents/INC_NOTFOUND")
    assert response.status_code == 404


def test_get_incident_report_wrong_customer(auth_client, db_session):
    """Test retrieving another customer's incident report fails"""
    # Create incident as authenticated customer
    create_response = auth_client.post(
        "/api/v1/incidents",
        json={
            "incident_category": "technical_issue",
            "incident_title": "Test",
            "incident_description": "Test",
            "severity": "low"
        }
    )
    incident_reference = create_response.json()["incident_reference"]

    # Manually create an incident for a different customer
    from datetime import datetime
    from app.models.incident import IncidentReport

    other_customer_id = uuid.uuid4()
    other_incident = IncidentReport(
        incident_report_id=uuid.uuid4(),
        customer_id=other_customer_id,
        incident_reference="INC_OTHER",
        incident_category="technical_issue",
        incident_title="Other customer incident",
        incident_description="Test",
        severity="low",
        status="reported",
        reported_at=datetime.now(datetime.now().astimezone().tzinfo),
        correlation_id="test_corr",
        created_at=datetime.now(datetime.now().astimezone().tzinfo),
        updated_at=datetime.now(datetime.now().astimezone().tzinfo)
    )
    db_session.add(other_incident)
    db_session.commit()

    # Try to retrieve other customer's incident
    get_response = auth_client.get("/api/v1/incidents/INC_OTHER")

    assert get_response.status_code == 404


def test_list_customer_incidents(auth_client):
    """Test listing incidents for authenticated customer"""
    # Create multiple incidents
    auth_client.post(
        "/api/v1/incidents",
        json={
            "incident_category": "technical_issue",
            "incident_title": "Issue 1",
            "incident_description": "Description 1",
            "severity": "low"
        }
    )

    auth_client.post(
        "/api/v1/incidents",
        json={
            "incident_category": "service_outage",
            "incident_title": "Issue 2",
            "incident_description": "Description 2",
            "severity": "high"
        }
    )

    # List incidents
    response = auth_client.get("/api/v1/incidents")

    assert response.status_code == 200
    data = response.json()
    assert isinstance(data, list)
    assert len(data) >= 2

    # Verify incidents belong to current customer
    titles = [incident["incident_title"] for incident in data]
    assert "Issue 1" in titles
    assert "Issue 2" in titles


def test_list_customer_incidents_unauthenticated(client):
    """Test listing incidents without authentication fails"""
    response = client.get("/api/v1/incidents")
    assert response.status_code == 403

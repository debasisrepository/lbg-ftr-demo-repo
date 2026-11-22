"""Tests for incident report service (BR-OPS-008)"""
import uuid
from datetime import datetime

import pytest

from app.core.errors import ValidationError
from app.services.incident_report_service import IncidentReportService


def test_create_incident_report_success(db_session, seeded_data):
    """Test creating a new incident report"""
    service = IncidentReportService(db_session)
    customer_id = uuid.UUID("10000000-0000-0000-0000-000000000001")

    incident = service.create_incident_report(
        customer_id=customer_id,
        incident_category="technical_issue",
        incident_title="Mobile app crashes on login",
        incident_description="The app crashes immediately after entering credentials",
        severity="high",
        correlation_id="test_corr_123"
    )

    assert incident is not None
    assert incident.incident_report_id is not None
    assert incident.customer_id == customer_id
    assert incident.incident_category == "technical_issue"
    assert incident.incident_title == "Mobile app crashes on login"
    assert incident.severity == "high"
    assert incident.status in ["reported", "acknowledged"]
    assert incident.incident_reference is not None
    assert incident.incident_reference.startswith("INC")
    assert incident.external_incident_ref is not None


def test_create_incident_report_all_categories(db_session, seeded_data):
    """Test creating incident reports with all valid categories"""
    service = IncidentReportService(db_session)
    customer_id = uuid.UUID("10000000-0000-0000-0000-000000000001")

    valid_categories = ['technical_issue', 'service_outage', 'data_issue', 'security_concern', 'other']

    for category in valid_categories:
        incident = service.create_incident_report(
            customer_id=customer_id,
            incident_category=category,
            incident_title=f"Test {category}",
            incident_description="Test description",
            severity="medium",
            correlation_id=f"test_corr_{category}"
        )
        assert incident.incident_category == category


def test_create_incident_report_all_severities(db_session, seeded_data):
    """Test creating incident reports with all valid severities"""
    service = IncidentReportService(db_session)
    customer_id = uuid.UUID("10000000-0000-0000-0000-000000000001")

    valid_severities = ['low', 'medium', 'high', 'critical']

    for severity in valid_severities:
        incident = service.create_incident_report(
            customer_id=customer_id,
            incident_category="technical_issue",
            incident_title=f"Test {severity} severity",
            incident_description="Test description",
            severity=severity,
            correlation_id=f"test_corr_{severity}"
        )
        assert incident.severity == severity


def test_create_incident_report_invalid_category(db_session, seeded_data):
    """Test creating incident report with invalid category"""
    service = IncidentReportService(db_session)
    customer_id = uuid.UUID("10000000-0000-0000-0000-000000000001")

    with pytest.raises(ValidationError) as exc_info:
        service.create_incident_report(
            customer_id=customer_id,
            incident_category="invalid_category",
            incident_title="Test",
            incident_description="Test",
            severity="medium",
            correlation_id="test_corr_invalid"
        )

    assert "Invalid incident category" in str(exc_info.value)


def test_create_incident_report_invalid_severity(db_session, seeded_data):
    """Test creating incident report with invalid severity"""
    service = IncidentReportService(db_session)
    customer_id = uuid.UUID("10000000-0000-0000-0000-000000000001")

    with pytest.raises(ValidationError) as exc_info:
        service.create_incident_report(
            customer_id=customer_id,
            incident_category="technical_issue",
            incident_title="Test",
            incident_description="Test",
            severity="extreme",
            correlation_id="test_corr_invalid"
        )

    assert "Invalid severity" in str(exc_info.value)


def test_create_incident_report_without_description(db_session, seeded_data):
    """Test creating incident report without description (optional field)"""
    service = IncidentReportService(db_session)
    customer_id = uuid.UUID("10000000-0000-0000-0000-000000000001")

    incident = service.create_incident_report(
        customer_id=customer_id,
        incident_category="technical_issue",
        incident_title="Test incident",
        incident_description=None,
        severity="low",
        correlation_id="test_corr_no_desc"
    )

    assert incident is not None
    assert incident.incident_description is None


def test_get_incident_report_by_reference(db_session, seeded_data):
    """Test retrieving incident report by reference"""
    service = IncidentReportService(db_session)
    customer_id = uuid.UUID("10000000-0000-0000-0000-000000000001")

    # Create incident
    created = service.create_incident_report(
        customer_id=customer_id,
        incident_category="data_issue",
        incident_title="Missing transaction",
        incident_description="Transaction not showing in history",
        severity="medium",
        correlation_id="test_corr_get"
    )

    # Retrieve it
    retrieved = service.get_incident_report(created.incident_reference)

    assert retrieved is not None
    assert retrieved.incident_report_id == created.incident_report_id
    assert retrieved.incident_reference == created.incident_reference


def test_get_incident_report_not_found(db_session, seeded_data):
    """Test retrieving non-existent incident report"""
    service = IncidentReportService(db_session)

    with pytest.raises(ValidationError) as exc_info:
        service.get_incident_report("INC_NOTFOUND")

    assert "not found" in str(exc_info.value).lower()


def test_list_customer_incidents(db_session, seeded_data):
    """Test listing incidents for a customer"""
    service = IncidentReportService(db_session)
    customer_id = uuid.UUID("10000000-0000-0000-0000-000000000001")

    # Create multiple incidents
    incident1 = service.create_incident_report(
        customer_id=customer_id,
        incident_category="technical_issue",
        incident_title="Issue 1",
        incident_description="Description 1",
        severity="low",
        correlation_id="test_corr_list_1"
    )

    incident2 = service.create_incident_report(
        customer_id=customer_id,
        incident_category="service_outage",
        incident_title="Issue 2",
        incident_description="Description 2",
        severity="high",
        correlation_id="test_corr_list_2"
    )

    # List incidents
    incidents = service.list_customer_incidents(customer_id)

    assert len(incidents) >= 2
    incident_ids = [i.incident_report_id for i in incidents]
    assert incident1.incident_report_id in incident_ids
    assert incident2.incident_report_id in incident_ids


def test_list_customer_incidents_empty(db_session, seeded_data):
    """Test listing incidents for customer with no incidents"""
    service = IncidentReportService(db_session)
    customer_id = uuid.uuid4()  # Non-existent customer

    incidents = service.list_customer_incidents(customer_id)

    assert incidents == []


def test_list_customer_incidents_respects_limit(db_session, seeded_data):
    """Test listing incidents respects limit parameter"""
    service = IncidentReportService(db_session)
    customer_id = uuid.UUID("10000000-0000-0000-0000-000000000001")

    # Create multiple incidents
    for i in range(5):
        service.create_incident_report(
            customer_id=customer_id,
            incident_category="technical_issue",
            incident_title=f"Issue {i}",
            incident_description=f"Description {i}",
            severity="low",
            correlation_id=f"test_corr_limit_{i}"
        )

    # List with limit
    incidents = service.list_customer_incidents(customer_id, limit=3)

    assert len(incidents) <= 3

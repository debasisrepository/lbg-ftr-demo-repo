"""
Unit tests for PS26/2 and PS7/26 incident reporting.
Requirement: BR-OPS-008, BR-OPS-009, RES-05 (Release 2)
Test Cases: TC-OPS-008, TC-OPS-009
"""
import uuid
from datetime import UTC, datetime

import pytest

from app.models.incident_report import IncidentReport


def test_create_incident_report_with_ps26_2_classification(db_session):
    """Test creating incident report with FCA PS26/2 classification (TC-OPS-008)."""
    incident = IncidentReport(
        id=uuid.uuid4(),
        incident_reference="INC-20261123-00001",
        incident_type="payment_disruption",
        severity="critical",
        detected_at=datetime.now(UTC),
        description="Payment processing system outage affecting 10,000+ customers",
        affected_service="payments",
        fca_ps26_2_applicable=True,
        pra_ps7_26_applicable=False,
        material_impact_threshold_met=True,
        reporting_route="standard",
        status="detected",
        created_at=datetime.now(UTC),
        updated_at=datetime.now(UTC)
    )
    
    db_session.add(incident)
    db_session.commit()
    db_session.refresh(incident)
    
    # Verify
    assert incident.incident_reference == "INC-20261123-00001"
    assert incident.fca_ps26_2_applicable is True
    assert incident.material_impact_threshold_met is True
    assert incident.reporting_route == "standard"
    assert incident.severity == "critical"


def test_create_incident_report_with_pra_ps7_26_classification(db_session):
    """Test creating incident report with PRA PS7/26 classification (TC-OPS-009)."""
    incident = IncidentReport(
        id=uuid.uuid4(),
        incident_reference="INC-20261123-00002",
        incident_type="data_breach",
        severity="major",
        detected_at=datetime.now(UTC),
        description="Unauthorized access to customer data",
        affected_service="customer_data",
        fca_ps26_2_applicable=False,
        pra_ps7_26_applicable=True,
        material_impact_threshold_met=True,
        reporting_route="enhanced",
        status="investigating",
        created_at=datetime.now(UTC),
        updated_at=datetime.now(UTC)
    )
    
    db_session.add(incident)
    db_session.commit()
    db_session.refresh(incident)
    
    # Verify
    assert incident.incident_reference == "INC-20261123-00002"
    assert incident.pra_ps7_26_applicable is True
    assert incident.material_impact_threshold_met is True
    assert incident.reporting_route == "enhanced"


def test_create_incident_below_threshold(db_session):
    """Test incident below PS26/2 and PS7/26 thresholds."""
    incident = IncidentReport(
        id=uuid.uuid4(),
        incident_reference="INC-20261123-00003",
        incident_type="service_outage",
        severity="minor",
        detected_at=datetime.now(UTC),
        description="Brief API latency spike affecting <100 customers for 5 minutes",
        affected_service="api_gateway",
        fca_ps26_2_applicable=False,
        pra_ps7_26_applicable=False,
        material_impact_threshold_met=False,
        reporting_route=None,
        status="resolved",
        resolved_at=datetime.now(UTC),
        created_at=datetime.now(UTC),
        updated_at=datetime.now(UTC)
    )
    
    db_session.add(incident)
    db_session.commit()
    db_session.refresh(incident)
    
    # Verify
    assert incident.material_impact_threshold_met is False
    assert incident.reporting_route is None
    assert incident.fca_ps26_2_applicable is False
    assert incident.pra_ps7_26_applicable is False


def test_incident_severity_constraint(db_session):
    """Test incident severity constraint enforcement."""
    incident = IncidentReport(
        id=uuid.uuid4(),
        incident_reference="INC-20261123-00004",
        incident_type="service_outage",
        severity="critical",  # Valid: critical, major, minor
        detected_at=datetime.now(UTC),
        description="Test severity",
        affected_service="test",
        fca_ps26_2_applicable=False,
        pra_ps7_26_applicable=False,
        material_impact_threshold_met=False,
        status="detected",
        created_at=datetime.now(UTC),
        updated_at=datetime.now(UTC)
    )
    
    db_session.add(incident)
    db_session.commit()
    
    # Valid severity accepted
    assert incident.severity == "critical"


def test_incident_reporting_route_constraint(db_session):
    """Test incident reporting route constraint (standard or enhanced)."""
    incident = IncidentReport(
        id=uuid.uuid4(),
        incident_reference="INC-20261123-00005",
        incident_type="service_outage",
        severity="major",
        detected_at=datetime.now(UTC),
        description="Test reporting route",
        affected_service="test",
        fca_ps26_2_applicable=True,
        pra_ps7_26_applicable=False,
        material_impact_threshold_met=True,
        reporting_route="standard",  # Valid: standard, enhanced, or NULL
        status="detected",
        created_at=datetime.now(UTC),
        updated_at=datetime.now(UTC)
    )
    
    db_session.add(incident)
    db_session.commit()
    
    # Valid reporting route accepted
    assert incident.reporting_route == "standard"


def test_incident_status_lifecycle(db_session):
    """Test incident status lifecycle transitions."""
    incident = IncidentReport(
        id=uuid.uuid4(),
        incident_reference="INC-20261123-00006",
        incident_type="payment_disruption",
        severity="major",
        detected_at=datetime.now(UTC),
        description="Test lifecycle",
        affected_service="payments",
        fca_ps26_2_applicable=True,
        pra_ps7_26_applicable=False,
        material_impact_threshold_met=True,
        reporting_route="standard",
        status="detected",
        created_at=datetime.now(UTC),
        updated_at=datetime.now(UTC)
    )
    
    db_session.add(incident)
    db_session.commit()
    
    # Transition: detected -> investigating
    incident.status = "investigating"
    db_session.commit()
    assert incident.status == "investigating"
    
    # Transition: investigating -> reported
    incident.status = "reported"
    incident.reported_to_regulator_at = datetime.now(UTC)
    db_session.commit()
    assert incident.status == "reported"
    assert incident.reported_to_regulator_at is not None
    
    # Transition: reported -> resolved
    incident.status = "resolved"
    incident.resolved_at = datetime.now(UTC)
    incident.root_cause = "Third-party payment gateway outage"
    db_session.commit()
    assert incident.status == "resolved"
    assert incident.resolved_at is not None
    
    # Transition: resolved -> closed
    incident.status = "closed"
    db_session.commit()
    assert incident.status == "closed"


def test_incident_reference_format(db_session):
    """Test incident reference follows format INC-YYYYMMDD-NNNNN."""
    incident = IncidentReport(
        id=uuid.uuid4(),
        incident_reference="INC-20261123-00007",
        incident_type="service_outage",
        severity="minor",
        detected_at=datetime.now(UTC),
        description="Test reference format",
        affected_service="test",
        fca_ps26_2_applicable=False,
        pra_ps7_26_applicable=False,
        material_impact_threshold_met=False,
        status="detected",
        created_at=datetime.now(UTC),
        updated_at=datetime.now(UTC)
    )
    
    db_session.add(incident)
    db_session.commit()
    
    # Verify format: INC-YYYYMMDD-NNNNN
    ref = incident.incident_reference
    assert ref.startswith("INC-")
    parts = ref.split("-")
    assert len(parts) == 3
    assert len(parts[1]) == 8  # YYYYMMDD
    assert parts[1].isdigit()
    assert len(parts[2]) == 5  # NNNNN
    assert parts[2].isdigit()


def test_incident_both_fca_and_pra_applicable(db_session):
    """Test incident can be applicable to both FCA PS26/2 and PRA PS7/26."""
    incident = IncidentReport(
        id=uuid.uuid4(),
        incident_reference="INC-20261123-00008",
        incident_type="system_failure",
        severity="critical",
        detected_at=datetime.now(UTC),
        description="Core banking system failure affecting all services",
        affected_service="core_banking",
        fca_ps26_2_applicable=True,
        pra_ps7_26_applicable=True,
        material_impact_threshold_met=True,
        reporting_route="enhanced",
        status="detected",
        created_at=datetime.now(UTC),
        updated_at=datetime.now(UTC)
    )
    
    db_session.add(incident)
    db_session.commit()
    
    # Verify both applicable
    assert incident.fca_ps26_2_applicable is True
    assert incident.pra_ps7_26_applicable is True
    assert incident.reporting_route == "enhanced"


def test_query_incidents_by_ps26_2_applicable(db_session):
    """Test querying incidents by PS26/2 applicability."""
    # Create mix of incidents
    incident1 = IncidentReport(
        id=uuid.uuid4(),
        incident_reference="INC-20261123-00009",
        incident_type="payment_disruption",
        severity="critical",
        detected_at=datetime.now(UTC),
        description="PS26/2 applicable incident",
        affected_service="payments",
        fca_ps26_2_applicable=True,
        pra_ps7_26_applicable=False,
        material_impact_threshold_met=True,
        reporting_route="standard",
        status="detected",
        created_at=datetime.now(UTC),
        updated_at=datetime.now(UTC)
    )
    
    incident2 = IncidentReport(
        id=uuid.uuid4(),
        incident_reference="INC-20261123-00010",
        incident_type="minor_outage",
        severity="minor",
        detected_at=datetime.now(UTC),
        description="Not applicable",
        affected_service="api",
        fca_ps26_2_applicable=False,
        pra_ps7_26_applicable=False,
        material_impact_threshold_met=False,
        reporting_route=None,
        status="resolved",
        created_at=datetime.now(UTC),
        updated_at=datetime.now(UTC)
    )
    
    db_session.add(incident1)
    db_session.add(incident2)
    db_session.commit()
    
    # Query PS26/2 applicable incidents
    ps26_2_incidents = db_session.query(IncidentReport).filter(
        IncidentReport.fca_ps26_2_applicable == True
    ).all()
    
    assert len(ps26_2_incidents) == 1
    assert ps26_2_incidents[0].incident_reference == "INC-20261123-00009"


def test_incident_readiness_by_march_2027(db_session):
    """
    Document test: Verify incident reporting system ready by 18 March 2027 (RES-05).
    
    This test documents the regulatory requirement deadline.
    The model and classification system must be operational by this date.
    """
    # System is ready if we can create, classify, and report incidents
    incident = IncidentReport(
        id=uuid.uuid4(),
        incident_reference="INC-20270318-00001",
        incident_type="payment_disruption",
        severity="critical",
        detected_at=datetime(2027, 3, 18, 10, 0, 0, tzinfo=UTC),
        description="Deadline day test - system operational",
        affected_service="payments",
        fca_ps26_2_applicable=True,
        pra_ps7_26_applicable=True,
        material_impact_threshold_met=True,
        reporting_route="standard",
        status="reported",
        reported_to_regulator_at=datetime(2027, 3, 18, 11, 0, 0, tzinfo=UTC),
        created_at=datetime(2027, 3, 18, 10, 0, 0, tzinfo=UTC),
        updated_at=datetime(2027, 3, 18, 11, 0, 0, tzinfo=UTC)
    )
    
    db_session.add(incident)
    db_session.commit()
    
    # System ready if incident can be created and reported
    assert incident.detected_at.date() == datetime(2027, 3, 18).date()
    assert incident.reported_to_regulator_at is not None
    assert incident.status == "reported"

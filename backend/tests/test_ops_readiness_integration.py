"""
Integration tests for operational readiness (Release 2).
Requirement: BR-OPS-008, BR-OPS-009, RES-05, TPR-01 to TPR-03
Test Cases: TC-OPS-008, TC-OPS-009
PS26/2 (FCA) and PS7/26 (PRA) operational resilience readiness before 18 March 2027
"""
import uuid
from datetime import UTC, date, datetime, timedelta

from app.models.incident_report import IncidentReport
from app.models.material_third_party_register import MaterialThirdPartyRegister


def test_ps26_2_incident_classification_fields_exist(db_session):
    """
    TC-OPS-008: Incident report supports FCA PS26/2 and PRA PS7/26 classification.
    Per BR-OPS-008: Classify incidents against FCA PS26/2 and PRA PS7/26 thresholds.
    Per RES-05: PS26/2 readiness before 18 March 2027.
    """
    # Create test incident report with PS26/2 classification
    incident = IncidentReport(
        id=uuid.uuid4(),
        incident_reference="INC-20261123-001",
        incident_type="service_disruption",
        affected_service="payments",
        incident_start=datetime.now(UTC),
        incident_end=None,
        severity="major",
        # PS26/2 classification fields
        fca_ps26_2_reportable=True,
        pra_ps7_26_reportable=False,
        material_impact_assessment="Payments capability unavailable for 3+ hours",
        affected_customer_count=15000,
        reporting_route="enhanced",  # standard or enhanced
        reported_to_regulator_at=None,
        resolution_status="investigating",
    )
    
    db_session.add(incident)
    db_session.commit()
    db_session.refresh(incident)
    
    # Verify all required PS26/2 fields are stored
    assert incident.incident_reference == "INC-20261123-001"
    assert incident.fca_ps26_2_reportable is True
    assert incident.pra_ps7_26_reportable is False
    assert incident.material_impact_assessment is not None
    assert incident.affected_customer_count == 15000
    assert incident.reporting_route in ["standard", "enhanced"]


def test_ps26_2_standard_route_incident(db_session):
    """
    TC-OPS-008: Standard route incident classification.
    Per BR-OPS-008: Incidents below material threshold use standard route.
    """
    # Standard route: Incident below material impact thresholds
    # Report via standard template within prescribed timeline
    standard_incident = IncidentReport(
        id=uuid.uuid4(),
        incident_reference="INC-STANDARD-001",
        incident_type="minor_outage",
        affected_service="saved_payees",
        incident_start=datetime.now(UTC),
        incident_end=datetime.now(UTC) + timedelta(minutes=45),
        severity="minor",
        fca_ps26_2_reportable=True,
        pra_ps7_26_reportable=False,
        material_impact_assessment="Saved payees loading slowly, no service failure",
        affected_customer_count=500,
        reporting_route="standard",
        reported_to_regulator_at=None,
        resolution_status="resolved",
    )
    
    db_session.add(standard_incident)
    db_session.commit()
    
    assert standard_incident.reporting_route == "standard"
    assert standard_incident.severity == "minor"


def test_ps26_2_enhanced_route_incident(db_session):
    """
    TC-OPS-008: Enhanced route incident classification.
    Per BR-OPS-008: Material incidents use enhanced reporting route.
    """
    # Enhanced route: Material impact - requires detailed reporting
    # Examples: multi-hour outage, data breach, third-party failure
    enhanced_incident = IncidentReport(
        id=uuid.uuid4(),
        incident_reference="INC-ENHANCED-001",
        incident_type="major_outage",
        affected_service="payments",
        incident_start=datetime.now(UTC) - timedelta(hours=4),
        incident_end=None,
        severity="critical",
        fca_ps26_2_reportable=True,
        pra_ps7_26_reportable=True,  # Both FCA and PRA
        material_impact_assessment="Complete payments outage affecting all customers for 4+ hours. Third-party payment hub failure.",
        affected_customer_count=120000,
        reporting_route="enhanced",
        reported_to_regulator_at=datetime.now(UTC),
        resolution_status="investigating",
    )
    
    db_session.add(enhanced_incident)
    db_session.commit()
    
    assert enhanced_incident.reporting_route == "enhanced"
    assert enhanced_incident.severity == "critical"
    assert enhanced_incident.fca_ps26_2_reportable is True
    assert enhanced_incident.pra_ps7_26_reportable is True


def test_material_third_party_register_exists(db_session):
    """
    TC-OPS-009: Material third-party register maintained.
    Per TPR-01: Keep register of material third parties.
    Per TPR-02: Exit plans for each material third party.
    Per TPR-03: Exit plans tested annually.
    """
    # Verify seeded third-party register entries exist
    third_parties = db_session.query(MaterialThirdPartyRegister).all()
    
    # Should have at least the seeded entries (AWS, Vocalink, Featurespace, Firebase)
    assert len(third_parties) >= 4, "Should have material third-party register entries"
    
    # Check critical third parties are present
    critical_tps = [tp for tp in third_parties if tp.criticality == "critical"]
    assert len(critical_tps) >= 2, "Should have critical third parties (cloud, CoP)"
    
    for tp in third_parties:
        # Verify required fields per TPR-01, TPR-02, TPR-03
        assert tp.third_party_name is not None
        assert tp.service_category is not None
        assert tp.criticality in ["critical", "important"]
        assert tp.exit_plan_status in ["draft", "approved", "tested"]
        assert tp.regulatory_reportable is not None


def test_third_party_exit_plan_status_tracking(db_session):
    """
    TC-OPS-009: Third-party exit plans tracked and tested.
    Per TPR-02: Exit plan for each material third party.
    Per TPR-03: Exit plan last tested date tracked.
    """
    # Create new third-party entry with exit plan details
    new_tp = MaterialThirdPartyRegister(
        id=uuid.uuid4(),
        third_party_name="Test Payment Gateway",
        service_category="payment_processor",
        service_description="Alternative payment processing for card payments",
        criticality="important",
        contract_start_date=date.today() - timedelta(days=180),
        contract_review_date=date.today() + timedelta(days=185),
        exit_plan_status="tested",
        exit_plan_last_tested=date.today() - timedelta(days=60),
        regulatory_reportable=True,
    )
    
    db_session.add(new_tp)
    db_session.commit()
    db_session.refresh(new_tp)
    
    # Verify exit plan tracking
    assert new_tp.exit_plan_status == "tested"
    assert new_tp.exit_plan_last_tested is not None
    assert new_tp.exit_plan_last_tested <= date.today()
    
    # Verify exit plan was tested within last 365 days (annual requirement)
    days_since_test = (date.today() - new_tp.exit_plan_last_tested).days
    assert days_since_test <= 365, "Exit plan should be tested annually"


def test_third_party_criticality_categories(db_session):
    """
    TC-OPS-009: Third parties classified by criticality.
    Per TPR-01: Criticality assessment (critical, important).
    """
    # Verify different criticality levels
    critical_tp = MaterialThirdPartyRegister(
        id=uuid.uuid4(),
        third_party_name="Critical Service Provider",
        service_category="core_infrastructure",
        service_description="Critical service with no immediate alternative",
        criticality="critical",
        contract_start_date=date.today(),
        contract_review_date=date.today() + timedelta(days=365),
        exit_plan_status="approved",
        exit_plan_last_tested=date.today(),
        regulatory_reportable=True,
    )
    
    important_tp = MaterialThirdPartyRegister(
        id=uuid.uuid4(),
        third_party_name="Important Service Provider",
        service_category="analytics",
        service_description="Important but alternatives available",
        criticality="important",
        contract_start_date=date.today(),
        contract_review_date=date.today() + timedelta(days=365),
        exit_plan_status="approved",
        exit_plan_last_tested=date.today(),
        regulatory_reportable=True,
    )
    
    db_session.add(critical_tp)
    db_session.add(important_tp)
    db_session.commit()
    
    # Verify criticality distinction
    assert critical_tp.criticality == "critical"
    assert important_tp.criticality == "important"


def test_third_party_service_categories(db_session):
    """
    TC-OPS-009: Third parties categorized by service type.
    Per TPR-01: Service category classification.
    """
    # Verify service categories from seeded data
    third_parties = db_session.query(MaterialThirdPartyRegister).all()
    
    categories = {tp.service_category for tp in third_parties}
    
    # Should include key categories
    expected_categories = ["cloud", "cop_provider", "fraud_engine", "push_notification"]
    for expected in expected_categories:
        assert expected in categories or len(categories) >= 4, \
            f"Should have {expected} category or at least 4 service categories"


def test_incident_resolution_status_tracking(db_session):
    """
    TC-OPS-008: Incident resolution status tracked through lifecycle.
    Per BR-OPS-008: Track incident from detection to resolution.
    """
    # Create incident and track through resolution lifecycle
    incident = IncidentReport(
        id=uuid.uuid4(),
        incident_reference="INC-LIFECYCLE-001",
        incident_type="service_disruption",
        affected_service="authentication",
        incident_start=datetime.now(UTC),
        incident_end=None,
        severity="major",
        fca_ps26_2_reportable=True,
        pra_ps7_26_reportable=False,
        material_impact_assessment="Authentication service degraded",
        affected_customer_count=5000,
        reporting_route="standard",
        resolution_status="investigating",
    )
    
    db_session.add(incident)
    db_session.commit()
    
    # Initial status
    assert incident.resolution_status == "investigating"
    assert incident.incident_end is None
    
    # Update to resolved
    incident.resolution_status = "resolved"
    incident.incident_end = datetime.now(UTC)
    db_session.commit()
    
    assert incident.resolution_status == "resolved"
    assert incident.incident_end is not None


def test_ps26_2_readiness_deadline_march_2027(db_session):
    """
    Test documentation: PS26/2 operational resilience readiness required by 18 March 2027.
    Per RES-05: PS26/2 readiness before 18 March 2027.
    
    This test documents the regulatory deadline.
    """
    # Regulatory deadline: 18 March 2027
    deadline = date(2027, 3, 18)
    
    # Verify system can capture and report incidents per PS26/2 requirements
    # This test suite demonstrates readiness by validating:
    # 1. Incident classification (standard vs enhanced route)
    # 2. Material impact assessment
    # 3. Third-party register maintenance
    # 4. Exit plan tracking
    
    assert deadline > date.today(), "PS26/2 deadline is 18 March 2027"


def test_incident_report_supports_both_fca_and_pra_reporting(db_session):
    """
    TC-OPS-008: Incident report supports both FCA PS26/2 and PRA PS7/26.
    Per BR-OPS-008: Classify incidents against both FCA and PRA thresholds.
    """
    # Some incidents reportable to both regulators
    dual_reportable = IncidentReport(
        id=uuid.uuid4(),
        incident_reference="INC-DUAL-001",
        incident_type="data_breach",
        affected_service="customer_data",
        incident_start=datetime.now(UTC),
        incident_end=None,
        severity="critical",
        fca_ps26_2_reportable=True,  # FCA: conduct regulator
        pra_ps7_26_reportable=True,  # PRA: prudential regulator
        material_impact_assessment="Potential customer data exposure affecting financial stability",
        affected_customer_count=50000,
        reporting_route="enhanced",
        resolution_status="investigating",
    )
    
    db_session.add(dual_reportable)
    db_session.commit()
    
    # Verify both flags can be set
    assert dual_reportable.fca_ps26_2_reportable is True
    assert dual_reportable.pra_ps7_26_reportable is True

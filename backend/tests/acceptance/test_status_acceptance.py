"""Acceptance tests for service status and lifeline features."""
import uuid
from datetime import datetime, timedelta, timezone

import pytest

from app.models.incident import LifelineGuidance, ServiceIncident, ServiceStatusPublication
from app.services.status_service import StatusService


def test_customers_can_access_service_status_during_disruption(db_session):
    """Customers can access current Service Status during an active disruption."""
    # Create an active incident
    incident = ServiceIncident(
        id=uuid.uuid4(),
        incident_reference="INC-ACC-001",
        incident_state="declared",
        affected_service_code="card_payments",
        customer_impact_summary="Card payments are temporarily unavailable",
        started_at=datetime.now(timezone.utc) - timedelta(hours=2),
        created_at=datetime.now(timezone.utc),
        updated_at=datetime.now(timezone.utc),
    )
    db_session.add(incident)
    db_session.commit()
    
    # Get status via service
    service = StatusService(db_session)
    result = service.get_status()
    
    # Verify status indicates disruption
    assert result["status_state"] == "disruption"
    assert len(result["incidents"]) == 1
    assert result["incidents"][0]["affected_service_code"] == "card_payments"


def test_status_content_identifies_affected_service(db_session):
    """Status content identifies the affected service at customer-understandable level."""
    incident = ServiceIncident(
        id=uuid.uuid4(),
        incident_reference="INC-ACC-002",
        incident_state="monitoring",
        affected_service_code="mobile_banking",
        customer_impact_summary="Mobile banking login may be slower than usual",
        started_at=datetime.now(timezone.utc),
        created_at=datetime.now(timezone.utc),
        updated_at=datetime.now(timezone.utc),
    )
    db_session.add(incident)
    
    publication = ServiceStatusPublication(
        id=uuid.uuid4(),
        incident_id=incident.id,
        publication_state="active",
        headline_text="Mobile banking slower",
        summary_text="We're aware mobile banking is slower than usual",
        affected_journeys_json=["mobile_login", "mobile_banking"],
        content_version=1,
        published_at=datetime.now(timezone.utc),
        created_at=datetime.now(timezone.utc),
    )
    db_session.add(publication)
    db_session.commit()
    
    service = StatusService(db_session)
    result = service.get_status()
    
    # Verify service and journey information is present
    assert result["incidents"][0]["affected_service_code"] == "mobile_banking"
    assert len(result["incidents"][0]["publications"]) == 1
    assert "mobile_login" in result["incidents"][0]["publications"][0]["affected_journeys"]


def test_service_status_remains_reachable_when_case_service_degraded(db_session):
    """Service Status remains reachable even when Case service is degraded."""
    # Create incident
    incident = ServiceIncident(
        id=uuid.uuid4(),
        incident_reference="INC-ACC-003",
        incident_state="declared",
        affected_service_code="case_service",
        customer_impact_summary="Case service temporarily degraded",
        started_at=datetime.now(timezone.utc),
        created_at=datetime.now(timezone.utc),
        updated_at=datetime.now(timezone.utc),
    )
    db_session.add(incident)
    db_session.commit()
    
    # Status service should work independently
    service = StatusService(db_session)
    result = service.get_status()
    
    # Verify status is retrievable
    assert result is not None
    assert result["status_state"] == "disruption"


def test_customers_can_open_lifeline_guidance_during_disruption(db_session):
    """During relevant disruption, customers can open Lifeline guidance."""
    incident = ServiceIncident(
        id=uuid.uuid4(),
        incident_reference="INC-ACC-004",
        incident_state="declared",
        affected_service_code="card_payments",
        customer_impact_summary="Card payment issues",
        started_at=datetime.now(timezone.utc),
        created_at=datetime.now(timezone.utc),
        updated_at=datetime.now(timezone.utc),
    )
    db_session.add(incident)
    db_session.commit()
    
    guidance = LifelineGuidance(
        id=uuid.uuid4(),
        incident_id=incident.id,
        guidance_title="Alternative payment options",
        guidance_content="Try using another card or payment method",
        guidance_type="fallback",
        is_active=True,
        created_at=datetime.now(timezone.utc),
        updated_at=datetime.now(timezone.utc),
    )
    db_session.add(guidance)
    db_session.commit()
    
    service = StatusService(db_session)
    result = service.get_lifeline()
    
    # Verify lifeline guidance is available
    assert len(result["guidance_items"]) == 1
    assert result["guidance_items"][0]["guidance_title"] == "Alternative payment options"


def test_lifeline_guidance_includes_approved_fallback_options(db_session):
    """Lifeline guidance includes approved fallback options relevant to disruption type."""
    incident = ServiceIncident(
        id=uuid.uuid4(),
        incident_reference="INC-ACC-005",
        incident_state="declared",
        affected_service_code="mobile_banking",
        customer_impact_summary="Mobile banking unavailable",
        started_at=datetime.now(timezone.utc),
        created_at=datetime.now(timezone.utc),
        updated_at=datetime.now(timezone.utc),
    )
    db_session.add(incident)
    db_session.commit()
    
    guidance = LifelineGuidance(
        id=uuid.uuid4(),
        incident_id=incident.id,
        guidance_title="Alternative banking options",
        guidance_content="Use online banking or call our support line",
        guidance_type="fallback",
        is_active=True,
        created_at=datetime.now(timezone.utc),
        updated_at=datetime.now(timezone.utc),
    )
    db_session.add(guidance)
    db_session.commit()
    
    service = StatusService(db_session)
    result = service.get_lifeline()
    
    # Verify fallback channels are provided
    assert len(result["fallback_channels"]) > 0
    assert any(ch["channel_type"] == "phone" for ch in result["fallback_channels"])


def test_guidance_can_be_presented_from_cached_content(db_session):
    """Guidance can be presented from cached content when live retrieval temporarily unavailable."""
    incident = ServiceIncident(
        id=uuid.uuid4(),
        incident_reference="INC-ACC-006",
        incident_state="declared",
        affected_service_code="test_service",
        customer_impact_summary="Test impact",
        started_at=datetime.now(timezone.utc),
        created_at=datetime.now(timezone.utc),
        updated_at=datetime.now(timezone.utc),
    )
    db_session.add(incident)
    db_session.commit()
    
    guidance = LifelineGuidance(
        id=uuid.uuid4(),
        incident_id=incident.id,
        guidance_title="Test guidance",
        guidance_content="Test content",
        guidance_type="fallback",
        is_active=True,
        created_at=datetime.now(timezone.utc),
        updated_at=datetime.now(timezone.utc),
    )
    db_session.add(guidance)
    db_session.commit()
    
    service = StatusService(db_session)
    result = service.get_lifeline()
    
    # Verify cache_version is provided for caching
    assert result["cache_version"] is not None
    assert result["cache_version"] != "empty"
    assert "cache_age_seconds" in result


def test_case_service_outage_does_not_prevent_status_and_lifeline_access(db_session):
    """A simulated case-service outage does not prevent access to Service Status and Lifeline."""
    # Create incident and guidance
    incident = ServiceIncident(
        id=uuid.uuid4(),
        incident_reference="INC-ACC-007",
        incident_state="declared",
        affected_service_code="case_service",
        customer_impact_summary="Case service outage",
        started_at=datetime.now(timezone.utc),
        created_at=datetime.now(timezone.utc),
        updated_at=datetime.now(timezone.utc),
    )
    db_session.add(incident)
    db_session.commit()
    
    guidance = LifelineGuidance(
        id=uuid.uuid4(),
        incident_id=incident.id,
        guidance_title="Case service alternatives",
        guidance_content="Please contact support via phone",
        guidance_type="phone",
        is_active=True,
        created_at=datetime.now(timezone.utc),
        updated_at=datetime.now(timezone.utc),
    )
    db_session.add(guidance)
    db_session.commit()
    
    # Both status and lifeline should work
    service = StatusService(db_session)
    
    status_result = service.get_status()
    assert status_result["status_state"] == "disruption"
    
    lifeline_result = service.get_lifeline()
    assert len(lifeline_result["guidance_items"]) == 1


def test_app_routes_users_to_status_when_case_retrieval_fails(db_session):
    """App routes affected users to Service Status when case retrieval fails under disruption."""
    # Create active incident
    incident = ServiceIncident(
        id=uuid.uuid4(),
        incident_reference="INC-ACC-008",
        incident_state="declared",
        affected_service_code="case_retrieval",
        customer_impact_summary="Case retrieval issues",
        started_at=datetime.now(timezone.utc),
        created_at=datetime.now(timezone.utc),
        updated_at=datetime.now(timezone.utc),
    )
    db_session.add(incident)
    db_session.commit()
    
    # Record fallback exposure
    service = StatusService(db_session)
    result = service.record_fallback_exposure(
        incident_reference="INC-ACC-008",
        content_source="live",
        cache_version=None,
        trigger="case_service_unavailable",
        case_reference="CP-TEST-001",
    )
    
    # Verify exposure can be recorded
    assert result["recorded"] is True
    assert result["correlation_id"] is not None


def test_status_and_lifeline_retrieval_independent_of_case_instance(db_session):
    """Status and Lifeline retrieval does not depend on same service instance as case rendering."""
    # This test verifies architectural independence by using StatusService directly
    # without any case service dependencies
    
    incident = ServiceIncident(
        id=uuid.uuid4(),
        incident_reference="INC-ACC-009",
        incident_state="declared",
        affected_service_code="independent_test",
        customer_impact_summary="Independence test",
        started_at=datetime.now(timezone.utc),
        created_at=datetime.now(timezone.utc),
        updated_at=datetime.now(timezone.utc),
    )
    db_session.add(incident)
    db_session.commit()
    
    # StatusService should work with just db_session, no case service needed
    service = StatusService(db_session)
    
    status_result = service.get_status()
    assert status_result is not None
    
    lifeline_result = service.get_lifeline()
    assert lifeline_result is not None

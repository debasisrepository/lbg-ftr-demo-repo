"""Unit tests for status service."""
import uuid
from datetime import datetime, timedelta, timezone

import pytest

from app.models.incident import LifelineGuidance, ServiceIncident, ServiceStatusPublication
from app.services.status_service import StatusService


def test_get_status_operational_when_no_incidents(db_session):
    """Test get_status returns operational when no active incidents."""
    service = StatusService(db_session)
    
    result = service.get_status()
    
    assert result["status_state"] == "operational"
    assert result["incidents"] == []
    assert result["lifeline_available"] is False
    assert result["cache_version"] is None
    assert result["max_age_seconds"] == 60


def test_get_status_disruption_when_active_incidents(db_session):
    """Test get_status returns disruption when active incidents exist."""
    # Create an active incident
    now = datetime.now(timezone.utc)
    incident = ServiceIncident(
        id=uuid.uuid4(),
        incident_reference="INC-TEST-001",
        incident_state="declared",
        affected_service_code="test_service",
        customer_impact_summary="Test impact",
        started_at=now - timedelta(hours=1),
        created_at=now,
        updated_at=now,
    )
    db_session.add(incident)
    db_session.commit()
    
    service = StatusService(db_session)
    result = service.get_status()
    
    assert result["status_state"] == "disruption"
    assert len(result["incidents"]) == 1
    assert result["incidents"][0]["incident_reference"] == "INC-TEST-001"
    assert result["cache_version"] is not None


def test_get_status_includes_publications(db_session):
    """Test get_status includes publications for incidents."""
    now = datetime.now(timezone.utc)
    incident = ServiceIncident(
        id=uuid.uuid4(),
        incident_reference="INC-TEST-001",
        incident_state="declared",
        affected_service_code="test_service",
        customer_impact_summary="Test impact",
        started_at=now - timedelta(hours=1),
        created_at=now,
        updated_at=now,
    )
    db_session.add(incident)
    db_session.commit()
    
    publication = ServiceStatusPublication(
        id=uuid.uuid4(),
        incident_id=incident.id,
        publication_state="active",
        headline_text="Test headline",
        summary_text="Test summary",
        affected_journeys_json=["journey1"],
        content_version=1,
        published_at=now,
        created_at=now,
    )
    db_session.add(publication)
    db_session.commit()
    
    service = StatusService(db_session)
    result = service.get_status()
    
    assert len(result["incidents"]) == 1
    assert len(result["incidents"][0]["publications"]) == 1
    assert result["incidents"][0]["publications"][0]["headline_text"] == "Test headline"


def test_get_status_filtered_by_service_code(db_session):
    """Test get_status can filter by affected_service_code."""
    now = datetime.now(timezone.utc)
    incident1 = ServiceIncident(
        id=uuid.uuid4(),
        incident_reference="INC-TEST-001",
        incident_state="declared",
        affected_service_code="service_a",
        customer_impact_summary="Test impact A",
        started_at=now,
        created_at=now,
        updated_at=now,
    )
    incident2 = ServiceIncident(
        id=uuid.uuid4(),
        incident_reference="INC-TEST-002",
        incident_state="declared",
        affected_service_code="service_b",
        customer_impact_summary="Test impact B",
        started_at=now,
        created_at=now,
        updated_at=now,
    )
    db_session.add_all([incident1, incident2])
    db_session.commit()
    
    service = StatusService(db_session)
    result = service.get_status(affected_service_code="service_a")
    
    assert len(result["incidents"]) == 1
    assert result["incidents"][0]["incident_reference"] == "INC-TEST-001"


def test_get_lifeline_empty_when_no_guidance(db_session):
    """Test get_lifeline returns empty when no guidance exists."""
    service = StatusService(db_session)
    
    result = service.get_lifeline()
    
    assert result["guidance_items"] == []
    assert result["protective_actions"] == []
    assert result["fallback_channels"] == []
    assert result["cache_version"] == "empty"


def test_get_lifeline_returns_guidance_items(db_session):
    """Test get_lifeline returns active guidance items."""
    now = datetime.now(timezone.utc)
    incident = ServiceIncident(
        id=uuid.uuid4(),
        incident_reference="INC-TEST-001",
        incident_state="declared",
        affected_service_code="test_service",
        customer_impact_summary="Test impact",
        started_at=now,
        created_at=now,
        updated_at=now,
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
        created_at=now,
        updated_at=now,
    )
    db_session.add(guidance)
    db_session.commit()
    
    service = StatusService(db_session)
    result = service.get_lifeline()
    
    assert len(result["guidance_items"]) == 1
    assert result["guidance_items"][0]["guidance_title"] == "Test guidance"
    assert result["cache_version"] != "empty"
    assert len(result["protective_actions"]) > 0
    assert len(result["fallback_channels"]) > 0


def test_get_lifeline_returns_none_for_matching_cached_version(db_session):
    """Test get_lifeline returns None when cached_version matches current."""
    now = datetime.now(timezone.utc)
    incident = ServiceIncident(
        id=uuid.uuid4(),
        incident_reference="INC-TEST-001",
        incident_state="declared",
        affected_service_code="test_service",
        customer_impact_summary="Test impact",
        started_at=now,
        created_at=now,
        updated_at=now,
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
        created_at=now,
        updated_at=now,
    )
    db_session.add(guidance)
    db_session.commit()
    
    service = StatusService(db_session)
    
    # Get the cache version
    result1 = service.get_lifeline()
    cache_version = result1["cache_version"]
    
    # Request again with the same cache version
    result2 = service.get_lifeline(cached_version=cache_version)
    
    assert result2 is None


def test_record_fallback_exposure_returns_success(db_session):
    """Test record_fallback_exposure returns success."""
    service = StatusService(db_session)
    
    result = service.record_fallback_exposure(
        incident_reference="INC-TEST-001",
        content_source="cached",
        cache_version="v123",
        trigger="case_service_unavailable",
        case_reference="CP-TEST-001",
    )
    
    assert result["recorded"] is True
    assert result["correlation_id"] is not None

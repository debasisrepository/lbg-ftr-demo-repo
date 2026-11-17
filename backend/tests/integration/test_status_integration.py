"""Integration tests for status endpoints."""
import uuid
from datetime import datetime, timedelta, timezone

import pytest

from app.models.incident import LifelineGuidance, ServiceIncident, ServiceStatusPublication


def test_get_status_endpoint_operational(client, db_session):
    """Test GET /api/v1/status returns operational when no incidents."""
    response = client.get("/api/v1/status")
    
    assert response.status_code == 200
    data = response.json()
    assert data["status_state"] == "operational"
    assert data["incidents"] == []
    assert data["lifeline_available"] is False


def test_get_status_endpoint_with_incidents(client, db_session):
    """Test GET /api/v1/status returns incidents."""
    # Create an active incident
    incident = ServiceIncident(
        id=uuid.uuid4(),
        incident_reference="INC-INT-001",
        incident_state="declared",
        affected_service_code="test_service",
        customer_impact_summary="Integration test impact",
        started_at=datetime.now(timezone.utc) - timedelta(hours=1),
        created_at=datetime.now(timezone.utc),
        updated_at=datetime.now(timezone.utc),
    )
    db_session.add(incident)
    
    # Create a publication
    publication = ServiceStatusPublication(
        id=uuid.uuid4(),
        incident_id=incident.id,
        publication_state="active",
        headline_text="Integration test headline",
        summary_text="Integration test summary",
        affected_journeys_json=["test_journey"],
        content_version=1,
        published_at=datetime.now(timezone.utc),
        created_at=datetime.now(timezone.utc),
    )
    db_session.add(publication)
    db_session.commit()
    
    response = client.get("/api/v1/status")
    
    assert response.status_code == 200
    data = response.json()
    assert data["status_state"] == "disruption"
    assert len(data["incidents"]) == 1
    assert data["incidents"][0]["incident_reference"] == "INC-INT-001"
    assert len(data["incidents"][0]["publications"]) == 1


def test_get_lifeline_endpoint_empty(client, db_session):
    """Test GET /api/v1/lifeline returns empty when no guidance."""
    response = client.get("/api/v1/lifeline")
    
    assert response.status_code == 200
    data = response.json()
    assert data["guidance_items"] == []
    assert data["cache_version"] == "empty"


def test_get_lifeline_endpoint_with_guidance(client, db_session):
    """Test GET /api/v1/lifeline returns guidance items."""
    # Create incident and guidance
    incident = ServiceIncident(
        id=uuid.uuid4(),
        incident_reference="INC-INT-001",
        incident_state="declared",
        affected_service_code="test_service",
        customer_impact_summary="Integration test impact",
        started_at=datetime.now(timezone.utc),
        created_at=datetime.now(timezone.utc),
        updated_at=datetime.now(timezone.utc),
    )
    db_session.add(incident)
    db_session.commit()
    
    guidance = LifelineGuidance(
        id=uuid.uuid4(),
        incident_id=incident.id,
        guidance_title="Integration test guidance",
        guidance_content="Integration test content",
        guidance_type="fallback",
        is_active=True,
        created_at=datetime.now(timezone.utc),
        updated_at=datetime.now(timezone.utc),
    )
    db_session.add(guidance)
    db_session.commit()
    
    response = client.get("/api/v1/lifeline")
    
    assert response.status_code == 200
    data = response.json()
    assert len(data["guidance_items"]) == 1
    assert data["guidance_items"][0]["guidance_title"] == "Integration test guidance"
    assert data["cache_version"] != "empty"


def test_get_lifeline_endpoint_304_not_modified(client, db_session):
    """Test GET /api/v1/lifeline returns 304 when cached_version matches."""
    # Create incident and guidance
    incident = ServiceIncident(
        id=uuid.uuid4(),
        incident_reference="INC-INT-001",
        incident_state="declared",
        affected_service_code="test_service",
        customer_impact_summary="Integration test impact",
        started_at=datetime.now(timezone.utc),
        created_at=datetime.now(timezone.utc),
        updated_at=datetime.now(timezone.utc),
    )
    db_session.add(incident)
    db_session.commit()
    
    guidance = LifelineGuidance(
        id=uuid.uuid4(),
        incident_id=incident.id,
        guidance_title="Integration test guidance",
        guidance_content="Integration test content",
        guidance_type="fallback",
        is_active=True,
        created_at=datetime.now(timezone.utc),
        updated_at=datetime.now(timezone.utc),
    )
    db_session.add(guidance)
    db_session.commit()
    
    # Get the cache version
    response1 = client.get("/api/v1/lifeline")
    assert response1.status_code == 200
    cache_version = response1.json()["cache_version"]
    
    # Request with the same cache version
    response2 = client.get(f"/api/v1/lifeline?cached_version={cache_version}")
    
    assert response2.status_code == 304


def test_post_fallback_exposures_endpoint(client, db_session):
    """Test POST /api/v1/status/fallback-exposures records exposure."""
    request_body = {
        "incident_reference": "INC-INT-001",
        "content_source": "cached",
        "cache_version": "v123",
        "trigger": "case_service_unavailable",
        "case_reference": "CP-TEST-001",
    }
    
    response = client.post("/api/v1/status/fallback-exposures", json=request_body)
    
    assert response.status_code == 202
    data = response.json()
    assert data["recorded"] is True
    assert data["correlation_id"] is not None


def test_post_fallback_exposures_validation_error(client, db_session):
    """Test POST /api/v1/status/fallback-exposures validates required fields."""
    request_body = {
        "incident_reference": "INC-INT-001",
        # Missing required fields
    }
    
    response = client.post("/api/v1/status/fallback-exposures", json=request_body)
    
    assert response.status_code == 422

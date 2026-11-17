"""Service status and lifeline service."""
import hashlib
import uuid
from typing import Any

from sqlalchemy.orm import Session

from app.core.clock import Clock
from app.repositories.incident_repository import IncidentRepository


class StatusService:
    """Service for status and lifeline operations."""

    def __init__(self, db: Session):
        self.db = db
        self.repo = IncidentRepository(db)

    def get_status(self, affected_service_code: str | None = None) -> dict[str, Any]:
        """Get current service status.

        Returns:
            dict with status_state, incidents, lifeline_available, generated_at, cache_version, max_age_seconds
        """
        incidents = self.repo.active_incidents(affected_service_code)

        # Determine status state
        status_state = "disruption" if incidents else "operational"

        # Get publications for active incidents
        incident_ids = [inc.id for inc in incidents]
        publications = self.repo.latest_publications(incident_ids) if incident_ids else []

        # Build incident objects
        incident_list = []
        for incident in incidents:
            # Find publications for this incident
            inc_pubs = [p for p in publications if p.incident_id == incident.id]

            incident_obj = {
                "incident_reference": incident.incident_reference,
                "incident_state": incident.incident_state,
                "affected_service_code": incident.affected_service_code,
                "customer_impact_summary": incident.customer_impact_summary,
                "started_at": incident.started_at.isoformat(),
                "resolved_at": incident.resolved_at.isoformat() if incident.resolved_at else None,
                "publications": [
                    {
                        "headline_text": pub.headline_text,
                        "summary_text": pub.summary_text,
                        "affected_journeys": pub.affected_journeys_json,
                        "published_at": pub.published_at.isoformat(),
                    }
                    for pub in inc_pubs
                ],
            }
            incident_list.append(incident_obj)

        # Check if lifeline guidance is available for active incidents
        lifeline_available = False
        if incidents:
            lifeline_items = self.repo.lifeline_items()
            lifeline_available = len(lifeline_items) > 0

        # Calculate cache version as hash of incident references
        cache_version = None
        if incidents:
            incident_refs = sorted([inc.incident_reference for inc in incidents])
            cache_version = hashlib.md5("|".join(incident_refs).encode()).hexdigest()[:16]

        return {
            "status_state": status_state,
            "incidents": incident_list,
            "lifeline_available": lifeline_available,
            "generated_at": Clock.utcnow().isoformat(),
            "cache_version": cache_version,
            "max_age_seconds": 60,
        }

    def get_lifeline(self, incident_reference: str | None = None, cached_version: str | None = None) -> dict[str, Any]:
        """Get lifeline guidance.

        Args:
            incident_reference: Optional incident reference to filter by
            cached_version: If provided and matches current version, returns None (indicating 304)

        Returns:
            dict with guidance_items, protective_actions, fallback_channels, cache_version,
            cache_age_seconds, generated_at, withdrawn_cache_versions
            OR None if cached_version matches current version
        """
        items = self.repo.lifeline_items(incident_reference)

        if not items:
            # No guidance available
            return {
                "guidance_items": [],
                "protective_actions": [],
                "fallback_channels": [],
                "cache_version": "empty",
                "cache_age_seconds": 0,
                "generated_at": Clock.utcnow().isoformat(),
                "withdrawn_cache_versions": [],
            }

        # Calculate cache version
        item_ids = sorted([str(item.id) for item in items])
        cache_version = hashlib.md5("|".join(item_ids).encode()).hexdigest()[:16]

        # Check if cached version matches
        if cached_version and cached_version == cache_version:
            return None  # Indicates 304 Not Modified

        # Build guidance items
        guidance_list = []
        for item in items:
            guidance_list.append({
                "id": str(item.id),
                "incident_id": str(item.incident_id),
                "guidance_category": item.guidance_type,
                "guidance_title": item.guidance_title,
                "guidance_body": item.guidance_content,
                "published_at": item.created_at.isoformat(),
            })

        # Calculate cache age (time since newest item)
        newest_item = max(items, key=lambda x: x.created_at)
        now = Clock.utcnow()
        newest_time = newest_item.created_at
        # Handle timezone-naive datetime comparison
        if newest_time.tzinfo is None:
            from datetime import timezone
            newest_time = newest_time.replace(tzinfo=timezone.utc)
        cache_age_seconds = int((now - newest_time).total_seconds())

        # For sandbox, provide sample protective actions and fallback channels
        protective_actions = [
            "Do not share your security details with anyone",
            "Check your recent transactions for any unauthorized activity",
        ]

        fallback_channels = [
            {
                "channel_type": "phone",
                "label": "Call us",
                "contact_detail": "0345 300 0000",
                "availability_text": "24/7",
            },
            {
                "channel_type": "callback",
                "label": "Request a callback",
                "contact_detail": None,
                "availability_text": "During business hours",
            },
        ]

        return {
            "guidance_items": guidance_list,
            "protective_actions": protective_actions,
            "fallback_channels": fallback_channels,
            "cache_version": cache_version,
            "cache_age_seconds": cache_age_seconds,
            "generated_at": Clock.utcnow().isoformat(),
            "withdrawn_cache_versions": [],
        }

    def record_fallback_exposure(
        self,
        incident_reference: str | None,
        content_source: str,
        cache_version: str | None,
        trigger: str,
        case_reference: str | None,
    ) -> dict[str, Any]:
        """Record that fallback content was shown.

        This is best-effort logging for audit purposes.

        Returns:
            dict with recorded (bool) and correlation_id
        """
        correlation_id = str(uuid.uuid4())

        # In a real implementation, this would write to an audit table
        # For now, we just return success

        return {
            "recorded": True,
            "correlation_id": correlation_id,
        }

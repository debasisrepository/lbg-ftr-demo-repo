"""Incident repository for service status and lifeline."""
import uuid
from datetime import datetime

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.incident import LifelineGuidance, ServiceIncident, ServiceStatusPublication


class IncidentRepository:
    """Repository for service incidents and status publications."""

    def __init__(self, db: Session):
        self.db = db

    def active_incidents(self, affected_service_code: str | None = None) -> list[ServiceIncident]:
        """Get all active incidents (not resolved)."""
        query = select(ServiceIncident).where(ServiceIncident.incident_state != "resolved")
        if affected_service_code:
            query = query.where(ServiceIncident.affected_service_code == affected_service_code)
        return list(self.db.execute(query).scalars().all())

    def latest_publications(self, incident_ids: list[uuid.UUID]) -> list[ServiceStatusPublication]:
        """Get latest active publications for given incidents."""
        if not incident_ids:
            return []
        query = (
            select(ServiceStatusPublication)
            .where(
                ServiceStatusPublication.incident_id.in_(incident_ids),
                ServiceStatusPublication.publication_state == "active",
                ServiceStatusPublication.withdrawn_at.is_(None),
            )
            .order_by(ServiceStatusPublication.published_at.desc())
        )
        return list(self.db.execute(query).scalars().all())

    def lifeline_items(self, incident_reference: str | None = None) -> list[LifelineGuidance]:
        """Get active lifeline guidance items."""
        query = select(LifelineGuidance).where(LifelineGuidance.is_active == True)  # noqa: E712
        if incident_reference:
            # Join with ServiceIncident to filter by reference
            query = query.join(ServiceIncident, LifelineGuidance.incident_id == ServiceIncident.id).where(
                ServiceIncident.incident_reference == incident_reference
            )
        query = query.order_by(LifelineGuidance.guidance_type, LifelineGuidance.created_at.desc())
        return list(self.db.execute(query).scalars().all())

    def upsert_incident(
        self,
        incident_reference: str,
        incident_state: str,
        affected_service_code: str,
        customer_impact_summary: str | None,
        started_at: datetime,
        resolved_at: datetime | None,
    ) -> ServiceIncident:
        """Insert or update a service incident."""
        existing = self.db.execute(
            select(ServiceIncident).where(ServiceIncident.incident_reference == incident_reference)
        ).scalar_one_or_none()

        now = datetime.now()
        if existing:
            existing.incident_state = incident_state
            existing.affected_service_code = affected_service_code
            existing.customer_impact_summary = customer_impact_summary
            existing.started_at = started_at
            existing.resolved_at = resolved_at
            existing.updated_at = now
            self.db.flush()
            return existing
        else:
            incident = ServiceIncident(
                id=uuid.uuid4(),
                incident_reference=incident_reference,
                incident_state=incident_state,
                affected_service_code=affected_service_code,
                customer_impact_summary=customer_impact_summary,
                started_at=started_at,
                resolved_at=resolved_at,
                created_at=now,
                updated_at=now,
            )
            self.db.add(incident)
            self.db.flush()
            return incident

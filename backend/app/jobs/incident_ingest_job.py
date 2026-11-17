"""Incident ingest background job."""
import asyncio
import logging
from datetime import datetime

from sqlalchemy.orm import Session

from app.adapters.incident_adapter import IncidentAdapter
from app.config import settings
from app.database import get_db
from app.repositories.incident_repository import IncidentRepository

logger = logging.getLogger(__name__)


class IncidentIngestJob:
    """Background job to poll and ingest incidents from external system."""

    def __init__(self):
        self.adapter = IncidentAdapter()
        self.poll_interval = settings.incident_poll_seconds
        self.running = False

    async def start(self):
        """Start the background polling loop."""
        self.running = True
        logger.info(f"Starting incident ingest job (polling every {self.poll_interval}s)")
        
        while self.running:
            try:
                await self._ingest_cycle()
            except Exception as e:
                logger.error(f"Error in incident ingest cycle: {e}", exc_info=True)
            
            await asyncio.sleep(self.poll_interval)

    async def stop(self):
        """Stop the background polling loop."""
        logger.info("Stopping incident ingest job")
        self.running = False

    async def _ingest_cycle(self):
        """Perform one ingest cycle."""
        # Get database session
        db_gen = get_db()
        db: Session = next(db_gen)
        
        try:
            # Fetch incidents from adapter
            incidents = self.adapter.get_incidents()
            
            if not incidents:
                logger.debug("No incidents returned from adapter")
                return
            
            # Upsert each incident
            repo = IncidentRepository(db)
            for incident_data in incidents:
                repo.upsert_incident(
                    incident_reference=incident_data["incident_reference"],
                    incident_state=incident_data["incident_state"],
                    affected_service_code=incident_data["affected_service_code"],
                    customer_impact_summary=incident_data.get("customer_impact_summary"),
                    started_at=incident_data["started_at"],
                    resolved_at=incident_data.get("resolved_at"),
                )
            
            db.commit()
            logger.info(f"Ingested {len(incidents)} incidents")
            
        except Exception as e:
            db.rollback()
            logger.error(f"Failed to ingest incidents: {e}", exc_info=True)
            raise
        finally:
            db.close()


# Global instance
_job_instance = None


def get_job_instance() -> IncidentIngestJob:
    """Get or create the singleton job instance."""
    global _job_instance
    if _job_instance is None:
        _job_instance = IncidentIngestJob()
    return _job_instance

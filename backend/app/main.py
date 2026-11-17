"""FastAPI application factory."""
import asyncio
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.config import settings
from app.adapters.correspondence_adapter import CorrespondenceAdapter
from app.core.clock import Clock
from app.core.event_bus import event_bus
from app.database import get_db
from app.jobs.incident_ingest_job import get_job_instance
from app.jobs.continuity_refresh_job import get_job_instance as get_continuity_job_instance
from app.repositories.communication_repository import CommunicationRepository
from app.routers import auth, cases, colleague, health, notifications, status
from app.services.communication_service import (
    CommunicationService,
    NotificationDispatcher,
)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan."""
    # Startup: Subscribe event handlers
    # Create communication service and subscribe to case events
    # Note: In production, would use dependency injection from a service registry
    def handle_case_event(event_data: dict):
        """Handle case events for notification generation."""
        # Create a fresh database session for event handling
        db = next(get_db())
        try:
            repo = CommunicationRepository(db)
            dispatcher = NotificationDispatcher(CorrespondenceAdapter())
            service = CommunicationService(repo, dispatcher, Clock())
            service.handle_event(event_data)
            db.commit()
        except Exception as e:
            db.rollback()
            print(f"Error handling case event: {e}")
        finally:
            db.close()
    
    # Subscribe to case events
    event_bus.subscribe("CaseStatusChanged", handle_case_event)
    event_bus.subscribe("OwnerChanged", handle_case_event)
    event_bus.subscribe("ExpectedByChanged", handle_case_event)
    event_bus.subscribe("ProtectedActionRequested", handle_case_event)
    event_bus.subscribe("IncidentDeclared", handle_case_event)
    
    # Start incident ingest job
    incident_job = get_job_instance()
    incident_task = asyncio.create_task(incident_job.start())
    
    # Start continuity refresh job
    continuity_job = get_continuity_job_instance()
    continuity_task = asyncio.create_task(continuity_job.start())
    
    yield
    
    # Shutdown: Stop jobs
    await incident_job.stop()
    await continuity_job.stop()
    incident_task.cancel()
    continuity_task.cancel()
    try:
        await incident_task
        await continuity_task
    except asyncio.CancelledError:
        pass


def create_app() -> FastAPI:
    """Create FastAPI application."""
    app = FastAPI(
        title="LBG Clear Path API",
        version="0.1.0",
        docs_url="/docs" if settings.docs_enabled else None,
        redoc_url="/redoc" if settings.docs_enabled else None,
        lifespan=lifespan,
    )

    # CORS middleware
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.cors_origins_list,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    # Mount routers under /api/v1 prefix
    app.include_router(auth.router, prefix="/api/v1/auth", tags=["auth"])
    app.include_router(cases.router, prefix="/api/v1", tags=["cases"])
    app.include_router(colleague.router, prefix="/api/v1/colleague", tags=["colleague"])
    app.include_router(notifications.router, prefix="/api/v1", tags=["notifications"])
    app.include_router(status.router, prefix="/api/v1", tags=["status"])
    app.include_router(health.router, tags=["health"])

    return app


app = create_app()

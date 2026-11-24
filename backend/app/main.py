"""Main FastAPI application."""
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.core.config import settings
from app.core.logging import configure_logging
from app.middleware.auth_session import BearerCaptureMiddleware
from app.middleware.correlation import CorrelationIdMiddleware
from app.middleware.error_shape import error_shape_middleware
from app.middleware.request_log import RequestLogMiddleware
from app.routers import (
    audit_events,
    auth,
    customers,
    health,
    policy,
    promises,
    queue_items,
    workspace,
)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan events."""
    # Configure logging
    configure_logging()

    # Startup
    yield

    # Shutdown
    pass


# Create FastAPI app
app = FastAPI(
    title="LBG FTR Collections API",
    description="Intelligent Receivables and Collections Application",
    version="0.1.0",
    docs_url="/api/docs",
    redoc_url="/api/redoc",
    openapi_url="/api/openapi.json",
    lifespan=lifespan,
)

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins_list,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Add middleware (order matters: first added = outermost)
app.add_middleware(RequestLogMiddleware)
app.add_middleware(BearerCaptureMiddleware)
app.add_middleware(CorrelationIdMiddleware)
app.middleware("http")(error_shape_middleware)

# Health endpoints at root and API paths
app.include_router(health.router, tags=["health"])
app.include_router(health.router, prefix="/api", tags=["health"])
app.include_router(health.router, prefix="/api/v1", tags=["health"])

# API v1 routers
app.include_router(auth.router, prefix="/api/v1/auth", tags=["auth"])
app.include_router(workspace.router, prefix="/api/v1/workspace", tags=["workspace"])
app.include_router(queue_items.router, prefix="/api/v1/queue-items", tags=["queue-items"])
app.include_router(customers.router, prefix="/api/v1/customers", tags=["customers"])
app.include_router(promises.router, prefix="/api/v1/promises", tags=["promises"])
app.include_router(policy.router, prefix="/api/v1/policy", tags=["policy"])
app.include_router(audit_events.router, prefix="/api/v1/audit-events", tags=["audit"])

"""
FastAPI application entry point.
"""
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.exc import OperationalError

from app.config import settings
from app.database import engine
from app.middleware.correlation_middleware import CorrelationMiddleware
from app.middleware.error_handlers import (
    database_exception_handler,
    generic_exception_handler,
    validation_exception_handler,
)
from app.routers import accounts, auth, payees, payments, profiles, scam_reports, status


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan context manager."""
    # Startup
    print("Starting application...")
    yield
    # Shutdown
    print("Shutting down application...")


# Create FastAPI app
app = FastAPI(
    title="LBG FTR Demo Backend",
    description="Release 2 Mobile Banking Platform Backend API - Loans, Business Profiles and Scam Reporting",
    version="0.2.0",
    lifespan=lifespan,
)

# Add correlation middleware (before CORS)
app.add_middleware(CorrelationMiddleware)

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins_list,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Register exception handlers
app.add_exception_handler(RequestValidationError, validation_exception_handler)
app.add_exception_handler(OperationalError, database_exception_handler)
app.add_exception_handler(Exception, generic_exception_handler)

# Register routers with /api/v1 prefix
app.include_router(auth.router, prefix="/api/v1")
app.include_router(accounts.router, prefix="/api/v1/accounts", tags=["accounts"])
app.include_router(status.router, prefix="/api/v1/capability-statuses", tags=["status"])
app.include_router(payees.router, prefix="/api/v1", tags=["payees"])
app.include_router(payments.router, prefix="/api/v1/payments", tags=["payments"])
# Release 2: Profile management and scam reporting
app.include_router(profiles.router, prefix="/api/v1/profiles", tags=["profiles"])
app.include_router(scam_reports.router, prefix="/api/v1/scam-reports", tags=["scam-reports"])


# Health endpoints (no /api prefix per architecture contract)
@app.get("/health")
async def health_check():
    """
    E-13: GET /health — liveness
    Unauthenticated, no database round trip.
    """
    return {"status": "ok"}


@app.get("/health/ready")
async def readiness_check():
    """
    E-14: GET /health/ready — readiness
    Unauthenticated; checks database connectivity.
    """
    try:
        # Simple connectivity check
        from sqlalchemy import text
        with engine.connect() as conn:
            conn.execute(text("SELECT 1"))
        return {"status": "ok"}
    except Exception:
        # Return 503 with error response shape
        from fastapi import HTTPException, status
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Database unavailable"
        )

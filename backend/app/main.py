"""FastAPI application factory and lifespan"""
from collections.abc import AsyncIterator
from contextlib import asynccontextmanager

from fastapi import Depends, FastAPI, HTTPException, Request, Response
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session

from .config import settings
from .core.auth_middleware import AuthenticationMiddleware
from .core.errors import AppError, app_error_handler, generic_exception_handler, http_exception_handler
from .core.middleware import CorrelationIDMiddleware
from .database import get_db


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncIterator[None]:
    """Application lifespan: setup and teardown"""
    # Migrations are handled by Alembic (alembic upgrade head)
    # Do NOT use Base.metadata.create_all here - it breaks migration parity

    # M-005: Validate production configuration
    environment = getattr(settings, "environment", "development")
    if environment == "production":
        # Check for default secret key
        if "change-me" in settings.secret_key.lower():
            raise RuntimeError(
                "Production deployment detected with default SECRET_KEY. "
                "Set a strong secret key via SECRET_KEY environment variable."
            )
        
        # L-003: Check for stub adapters in production
        stub_adapters = [
            k for k, v in vars(settings).items()
            if k.startswith("adapter_mode_") and v == "stub"
        ]
        if stub_adapters:
            raise RuntimeError(
                f"Production deployment with stub adapters: {stub_adapters}. "
                "Configure live adapters via environment variables."
            )

    # Run seed data
    from .seed import seed_database
    seed_database()

    yield

    # Cleanup (if needed)


# Create FastAPI application
app = FastAPI(
    title="Sample Bank Mobile Payments MVP",
    version="0.1.0",
    description="Backend API for mobile payments application",
    lifespan=lifespan,
    docs_url="/api/v1/docs",
    redoc_url="/api/v1/redoc",
    openapi_url="/api/v1/openapi.json",
)

# Middleware (order matters: first added = last executed)
# Add authentication middleware (executed after CORS)
app.add_middleware(AuthenticationMiddleware)

# Add correlation ID middleware
app.add_middleware(CorrelationIDMiddleware)

# CORS must be outermost (added last to execute first)
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.get_cors_origins_list(),
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE", "PATCH"],  # L-001: Explicit methods
    allow_headers=["Authorization", "Content-Type", "X-Correlation-ID"],  # L-001: Explicit headers
)

# L-002: Add security headers middleware
@app.middleware("http")
async def add_security_headers(request: Request, call_next):
    """Add security headers to all responses"""
    response = await call_next(request)
    response.headers["Content-Security-Policy"] = "default-src 'self'; script-src 'self'"
    response.headers["X-Frame-Options"] = "DENY"
    response.headers["X-Content-Type-Options"] = "nosniff"
    response.headers["Strict-Transport-Security"] = "max-age=31536000; includeSubDomains"
    response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"
    return response


# Exception handlers
app.add_exception_handler(AppError, app_error_handler)
app.add_exception_handler(HTTPException, http_exception_handler)
app.add_exception_handler(Exception, generic_exception_handler)


# Note: Health check endpoints are now handled by the health router (/api/v1/health)


# Root endpoint
@app.get("/")
def root(db: Session = Depends(get_db)) -> dict[str, str]:
    """Root endpoint with database connectivity check"""
    from .models.ref_code import RefCode

    # Verify database connectivity by querying ref_code table
    try:
        db.query(RefCode).first()
        status = "running"
    except Exception:
        status = "database_unavailable"

    return {
        "service": "Sample Bank Mobile Payments MVP",
        "version": "0.1.0",
        "status": status
    }


# Routers (imported after app creation to avoid circular imports)
from .routers import accounts, auth, health, incidents, notifications, payees, payments, profiles, support  # noqa: E402

app.include_router(auth.router, prefix="/api/v1/auth", tags=["auth"])
app.include_router(profiles.router, prefix="/api/v1", tags=["profiles"])
app.include_router(accounts.router, prefix="/api/v1", tags=["accounts"])
app.include_router(payees.router, prefix="/api/v1", tags=["payees"])
app.include_router(payments.router, prefix="/api/v1/payments", tags=["payments"])
app.include_router(notifications.router, prefix="/api/v1/notifications", tags=["notifications"])
app.include_router(support.router, prefix="/api/v1/support", tags=["support"])
app.include_router(incidents.router, prefix="/api/v1", tags=["incidents"])
app.include_router(health.router, prefix="/api/v1/health", tags=["health"])

"""FastAPI application factory and lifespan"""
from collections.abc import AsyncIterator
from contextlib import asynccontextmanager

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware

from .config import settings
from .core.errors import AppError, app_error_handler, generic_exception_handler, http_exception_handler
from .core.middleware import CorrelationIDMiddleware


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncIterator[None]:
    """Application lifespan: setup and teardown"""
    # Migrations are handled by Alembic (alembic upgrade head)
    # Do NOT use Base.metadata.create_all here - it breaks migration parity

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

# Middleware
app.add_middleware(CorrelationIDMiddleware)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.get_cors_origins_list(),
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Exception handlers
app.add_exception_handler(AppError, app_error_handler)
app.add_exception_handler(HTTPException, http_exception_handler)
app.add_exception_handler(Exception, generic_exception_handler)


# Note: Health check endpoints are now handled by the health router (/api/v1/health)


# Root endpoint
@app.get("/")
def root() -> dict[str, str]:
    """Root endpoint"""
    return {
        "service": "Sample Bank Mobile Payments MVP",
        "version": "0.1.0",
        "status": "running"
    }


# Routers (imported after app creation to avoid circular imports)
from .routers import accounts, auth, health, notifications, payees, payments, profiles, support  # noqa: E402

app.include_router(auth.router, prefix="/api/v1/auth", tags=["auth"])
app.include_router(profiles.router, prefix="/api/v1", tags=["profiles"])
app.include_router(accounts.router, prefix="/api/v1", tags=["accounts"])
app.include_router(payees.router, prefix="/api/v1", tags=["payees"])
app.include_router(payments.router, prefix="/api/v1/payments", tags=["payments"])
app.include_router(notifications.router, prefix="/api/v1/notifications", tags=["notifications"])
app.include_router(support.router, prefix="/api/v1/support", tags=["support"])
app.include_router(health.router, prefix="/api/v1/health", tags=["health"])

"""FastAPI application factory."""
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.config import settings
from app.database import engine
from app.seed import seed_database, SessionLocal
from app.middleware.correlation_id import CorrelationIDMiddleware
from app.middleware.error_handlers import (
    authentication_error_handler,
    authorization_error_handler,
    validation_error_handler,
    rate_limit_error_handler
)
from app.common.errors import (
    AuthenticationError,
    AuthorizationError,
    ValidationError,
    RateLimitError
)
from app.routers import auth, sca, profiles, accounts, payees, payments


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan - startup and shutdown."""
    # Startup
    print("Starting application...")
    
    # Run seed data if in debug mode (local development)
    if settings.debug:
        print("Running seed data (debug mode)...")
        db = SessionLocal()
        try:
            seed_database(db)
        except Exception as e:
            print(f"Seed data error (continuing): {e}")
        finally:
            db.close()
    
    yield
    
    # Shutdown
    print("Shutting down application...")
    engine.dispose()


# Create FastAPI app
app = FastAPI(
    title="LBG FTR Demo - Digital Banking Payment Journey API",
    description="Backend API for payment journey platform",
    version="0.1.0",
    lifespan=lifespan,
    docs_url="/api/docs",
    redoc_url="/api/redoc",
    openapi_url="/api/openapi.json"
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins_list,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Correlation ID middleware
app.add_middleware(CorrelationIDMiddleware)

# Error handlers
app.add_exception_handler(AuthenticationError, authentication_error_handler)
app.add_exception_handler(AuthorizationError, authorization_error_handler)
app.add_exception_handler(ValidationError, validation_error_handler)
app.add_exception_handler(RateLimitError, rate_limit_error_handler)

# Register API routers
app.include_router(auth.router, prefix="/api/v1")
app.include_router(sca.router, prefix="/api/v1")
app.include_router(profiles.router, prefix="/api/v1")
app.include_router(accounts.router, prefix="/api/v1")
app.include_router(payees.router, prefix="/api/v1")
app.include_router(payments.router, prefix="/api/v1")


@app.get("/health")
def health_check():
    """Health check endpoint."""
    return {"status": "healthy"}


@app.get("/api/health")
def api_health_check():
    """API health check endpoint."""
    return {"status": "healthy", "service": "lbg-ftr-demo-backend"}

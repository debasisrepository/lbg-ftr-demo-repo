"""Health check router."""
from datetime import datetime, timezone

from fastapi import APIRouter, Depends, Response
from sqlalchemy import text
from sqlalchemy.orm import Session

from app.core.deps import get_db
from app.schemas.health_schemas import HealthCheckSchema, HealthResponse, ReadinessResponse

router = APIRouter()


@router.get("/health", response_model=HealthResponse, include_in_schema=False)
def health():
    """Liveness check - does not touch database."""
    return HealthResponse(
        status="ok",
        service="lbg-ftr-receivables",
        version="0.1.0",
        time=datetime.now(timezone.utc),
    )


@router.get("/health/ready", response_model=ReadinessResponse, include_in_schema=False)
def readiness(response: Response, db: Session = Depends(get_db)):
    """Readiness check - verifies database and migrations."""
    checks = []

    # Check database
    db_ok = False
    try:
        db.execute(text("SELECT 1"))
        db_ok = True
        checks.append(HealthCheckSchema(name="database", ok=True))
    except Exception as e:
        checks.append(HealthCheckSchema(name="database", ok=False, message=str(e)))

    # Check migrations (simple check - does users table exist)
    migrations_ok = False
    try:
        db.execute(text("SELECT 1 FROM users LIMIT 1"))
        migrations_ok = True
        checks.append(HealthCheckSchema(name="migrations", ok=True))
    except Exception as e:
        checks.append(HealthCheckSchema(name="migrations", ok=False, message=str(e)))

    # SAP adapter check (informational only)
    checks.append(HealthCheckSchema(name="sap_adapter", ok=True, informational=True, message="stub"))

    # Overall status
    critical_checks_ok = db_ok and migrations_ok
    status = "ready" if critical_checks_ok else "not_ready"
    status_code = 200 if critical_checks_ok else 503
    
    # Set the actual HTTP status code
    response.status_code = status_code

    return ReadinessResponse(status=status, checks=checks)

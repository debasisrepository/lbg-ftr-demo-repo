"""Health check endpoints"""
from fastapi import APIRouter, Depends
from sqlalchemy import text
from sqlalchemy.orm import Session

from ..database import get_db
from ..services.capability_health_registry import health_registry

router = APIRouter()


@router.get("", status_code=200)
def health_check(db: Session = Depends(get_db)):
    """Basic health check"""
    try:
        # Check database connectivity (direct SQL is acceptable for health checks)
        db.execute(text("SELECT 1"))
        return {"status": "ok"}
    except Exception as e:
        return {"status": "error", "detail": str(e)}


@router.get("/ready", status_code=200)
def readiness_check(db: Session = Depends(get_db)):
    """Readiness check with capability status"""
    try:
        # Check database connectivity (direct SQL is acceptable for health checks)
        db.execute(text("SELECT 1"))

        # Register basic capabilities
        health_registry.register_capability("database", "ok")
        health_registry.register_capability("payments", "ok")
        health_registry.register_capability("notifications", "ok")

        # Get all capability statuses
        capabilities = health_registry.get_all_statuses()
        is_healthy = health_registry.is_healthy()

        return {
            "status": "ready" if is_healthy else "degraded",
            "capabilities": [
                {
                    "name": cap.capability,
                    "status": cap.status,
                    "message": cap.message,
                    "last_check": cap.last_check.isoformat() if cap.last_check else None
                }
                for cap in capabilities
            ]
        }
    except Exception as e:
        return {
            "status": "error",
            "detail": str(e),
            "capabilities": []
        }

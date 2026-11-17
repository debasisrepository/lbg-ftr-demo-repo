"""Health check router."""
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import text
from sqlalchemy.orm import Session

from app.database import get_db

router = APIRouter()


@router.get("/health", status_code=200)
def health():
    """Liveness check."""
    return {"status": "ok"}


@router.get("/health/ready", status_code=200)
def ready(db: Session = Depends(get_db)):
    """Readiness check with DB connectivity."""
    try:
        db.execute(text("SELECT 1"))
        return {"status": "ready", "database": "connected"}
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail={"status": "not_ready", "database": "disconnected", "error": str(e)},
        )

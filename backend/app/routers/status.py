"""Status and lifeline router."""
from typing import Annotated, Any

from fastapi import APIRouter, Depends, HTTPException, Query, Response, status
from sqlalchemy.orm import Session

from app.database import get_db
from app.services.status_service import StatusService

router = APIRouter()


def get_status_service(db: Session = Depends(get_db)) -> StatusService:
    """Dependency to get status service."""
    return StatusService(db)


@router.get("/status")
def get_status(
    affected_service_code: Annotated[str | None, Query(max_length=60)] = None,
    service: StatusService = Depends(get_status_service),
) -> dict[str, Any]:
    """Get current service status.

    Returns status of active incidents and whether lifeline guidance is available.
    This endpoint is public and works independently of the case service.
    """
    try:
        result = service.get_status(affected_service_code)
        return result
    except Exception:
        # Return 503 on internal errors so client falls back to cached content
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Service status temporarily unavailable",
        )


@router.get("/lifeline")
def get_lifeline(
    response: Response,
    incident_reference: Annotated[str | None, Query(max_length=80)] = None,
    cached_version: Annotated[str | None, Query()] = None,
    service: StatusService = Depends(get_status_service),
) -> dict[str, Any]:
    """Get lifeline guidance for current disruptions.

    Returns guidance items, protective actions, and fallback channels.
    Supports conditional GET via cached_version parameter.
    """
    try:
        result = service.get_lifeline(incident_reference, cached_version)

        if result is None:
            # Cached version matches - return 304 Not Modified
            response.status_code = status.HTTP_304_NOT_MODIFIED
            return {}

        return result

    except Exception:
        # Return 503 on internal errors so client falls back to cached content
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Lifeline guidance temporarily unavailable",
        )


@router.post("/status/fallback-exposures", status_code=status.HTTP_202_ACCEPTED)
def record_fallback_exposure(
    request_body: dict[str, Any],
    service: StatusService = Depends(get_status_service),
) -> dict[str, Any]:
    """Record that status/lifeline content was shown due to fallback condition.

    This is best-effort logging. Always returns 202 even if recording fails internally.
    """
    try:
        # Validate required fields
        if "content_source" not in request_body or "trigger" not in request_body:
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail="content_source and trigger are required",
            )

        # Validate enums
        if request_body["content_source"] not in ["live", "cached"]:
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail="content_source must be 'live' or 'cached'",
            )

        if request_body["trigger"] not in ["case_service_unavailable", "customer_opened"]:
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail="trigger must be 'case_service_unavailable' or 'customer_opened'",
            )

        result = service.record_fallback_exposure(
            incident_reference=request_body.get("incident_reference"),
            content_source=request_body["content_source"],
            cache_version=request_body.get("cache_version"),
            trigger=request_body["trigger"],
            case_reference=request_body.get("case_reference"),
        )

        return result

    except HTTPException:
        raise
    except Exception:
        # Even on internal failure, return 202 with recorded=false
        # The client should not see errors for this best-effort endpoint
        return {
            "recorded": False,
            "correlation_id": None,
        }

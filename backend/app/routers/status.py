"""
Status router (E-06).
Requirement: FR-ACCT-001, FR-ACCT-003, FR-PAY-001, FR-PAY-011
"""
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.database import get_db
from app.middleware.auth_middleware import get_current_user
from app.middleware.correlation_middleware import get_correlation_id
from app.models.customer_profile_ref import CustomerProfileRef
from app.schemas.status_schemas import (
    CapabilityStatusItem,
    CapabilityStatusListResponse,
)
from app.services.capability_status_service import CapabilityStatusService

router = APIRouter()


@router.get("/", response_model=CapabilityStatusListResponse)
def get_capability_statuses(
    db: Session = Depends(get_db),
    current_user: CustomerProfileRef = Depends(get_current_user),
    correlation_id: str = Depends(get_correlation_id)
) -> CapabilityStatusListResponse:
    """
    E-06: GET /api/v1/capability-statuses - Get all capability statuses.
    
    Returns current status for each of:
    - accounts_overview
    - saved_payees
    - payments
    - payment_status
    
    Protected route: requires valid session via get_current_user.
    
    Returns:
        CapabilityStatusListResponse with 4 items (one per capability)
    
    Raises:
        401: Invalid or expired session
    """
    capability_service = CapabilityStatusService(db)
    
    statuses = capability_service.get_all_capability_statuses()
    
    items = [
        CapabilityStatusItem(
            capability_name=status.capability_name,
            status_value=status.status_value,
            customer_message_code=status.customer_message_code,
            customer_message=_get_customer_message(status),
            recovery_guidance=_get_recovery_guidance(status),
            effective_from=status.effective_from
        )
        for status in statuses
    ]
    
    return CapabilityStatusListResponse(
        items=items,
        total=len(items),
        page=1,
        page_size=len(items)
    )


def _get_customer_message(status) -> str:
    """Get plain-language customer message for capability status."""
    capability_messages = {
        "accounts_overview": {
            "healthy": "Account overview is available",
            "stale": "Account data may be out of date",
            "partial": "Some account data is unavailable",
            "unavailable": "Account overview is currently unavailable",
            "restricted": "Account overview is restricted"
        },
        "saved_payees": {
            "healthy": "Saved payees are available",
            "stale": "Payee data may be out of date",
            "partial": "Some payee data is unavailable",
            "unavailable": "Saved payees are currently unavailable",
            "restricted": "Saved payees are restricted"
        },
        "payments": {
            "healthy": "Payments are available",
            "stale": "Payment service may be delayed",
            "partial": "Some payment features are unavailable",
            "unavailable": "Payments are currently unavailable",
            "restricted": "Payments are restricted"
        },
        "payment_status": {
            "healthy": "Payment status is available",
            "stale": "Payment status may be out of date",
            "partial": "Some payment status data is unavailable",
            "unavailable": "Payment status is currently unavailable",
            "restricted": "Payment status is restricted"
        }
    }
    
    messages = capability_messages.get(status.capability_name, {})
    return messages.get(status.status_value, f"{status.capability_name} status is {status.status_value}")


def _get_recovery_guidance(status) -> str:
    """Get recovery guidance for non-healthy states."""
    if status.status_value == "healthy":
        return ""
    elif status.status_value in ("stale", "partial"):
        return "Data will be updated automatically. Try refreshing in a few moments."
    elif status.status_value == "unavailable":
        return "Please try again later. If the problem persists, contact support."
    elif status.status_value == "restricted":
        return "Contact support for assistance."
    return "Please try again later."

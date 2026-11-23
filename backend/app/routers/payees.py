"""
Payees router for E-05 GET /api/v1/payees
Requirement: FR-PAY-001
"""
from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.adapters.entitlement_sandbox_adapter import EntitlementSandboxAdapter
from app.database import get_db
from app.middleware.auth_middleware import get_current_user
from app.middleware.correlation_middleware import get_correlation_id
from app.models.customer_profile_ref import CustomerProfileRef
from app.repositories.capability_status_repository import CapabilityStatusRepository
from app.repositories.payee_repository import PayeeRepository
from app.schemas.payees_schemas import PayeeListResponse
from app.services.payee_service import PayeeService

router = APIRouter()


@router.get("/payees", response_model=PayeeListResponse)
def get_saved_payees(
    page: int = Query(1, ge=1, description="Page number (1-based)"),
    page_size: int = Query(20, ge=1, le=50, description="Items per page"),
    db: Session = Depends(get_db),
    current_user: CustomerProfileRef = Depends(get_current_user),
    correlation_id: str = Depends(get_correlation_id)
) -> PayeeListResponse:
    """
    E-05: GET /api/v1/payees - View and select saved payees
    
    Returns saved payees available to the customer for payment entry.
    Only payees with payee_status saved_active that entitlement allows are returned.
    
    When saved_payees capability is unavailable, returns 200 with empty page
    and capability message explaining the unavailability.
    
    Full account numbers are never shown; only masked_account_identifier is returned.
    
    Args:
        page: Page number (1-based, default 1)
        page_size: Items per page (1-50, default 20)
        db: Database session
        current_user: Authenticated user from bearer token
        correlation_id: Correlation ID for tracing
        
    Returns:
        PayeeListResponse with items, total, page, page_size, capability
        
    Raises:
        401: session_invalid
        403: entitlement_denied (handled by empty page response)
        422: validation_error
        500: internal_error
    """
    # Initialize dependencies
    payee_repo = PayeeRepository(db)
    capability_repo = CapabilityStatusRepository(db)
    entitlement_adapter = EntitlementSandboxAdapter(db)
    
    # Create service
    service = PayeeService(payee_repo, capability_repo, entitlement_adapter)
    
    # Get saved payees
    return service.get_saved_payees_for_customer(
        customer_profile_ref_id=current_user.id,
        page=page,
        page_size=page_size
    )

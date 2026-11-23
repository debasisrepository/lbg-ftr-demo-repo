"""
Accounts router (E-04).
Requirement: FR-ACCT-001, FR-ACCT-002, FR-ACCT-003
"""
from typing import Annotated

from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.database import get_db
from app.middleware.auth_middleware import get_current_user
from app.middleware.correlation_middleware import get_correlation_id
from app.models.customer_profile_ref import CustomerProfileRef
from app.schemas.accounts_schemas import AccountOverviewResponse
from app.services.account_service import AccountService

router = APIRouter()


@router.get("/", response_model=AccountOverviewResponse)
def get_accounts_overview(
    page: Annotated[int, Query(ge=1)] = 1,
    page_size: Annotated[int, Query(ge=1, le=50)] = 20,
    db: Session = Depends(get_db),
    current_user: CustomerProfileRef = Depends(get_current_user),
    correlation_id: str = Depends(get_correlation_id)
) -> AccountOverviewResponse:
    """
    E-04: GET /api/v1/accounts - Accounts overview with honest freshness.
    
    Returns paginated account list with:
    - Balance with availability_state (never missing balance as zero)
    - as_of_timestamp and freshness_status per account
    - freshness_text in accessible plain language
    - item_state (available or partial)
    - overview_state (complete, partial, unavailable)
    - capability status for accounts_overview
    
    Protected route: requires valid session via get_current_user.
    Entitlement checked per request via EntitlementSandboxAdapter.
    
    Returns:
        AccountOverviewResponse with items, pagination, overview_state, capability
    
    Raises:
        401: Invalid or expired session
        403: Not entitled to view accounts
        422: Invalid pagination parameters
    """
    account_service = AccountService(db)
    
    return account_service.get_accounts_overview(
        customer_id=current_user.id,
        page=page,
        page_size=page_size
    )

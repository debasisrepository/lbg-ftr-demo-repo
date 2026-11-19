"""Account router."""
from fastapi import APIRouter, Depends, HTTPException, Query, Request
from sqlalchemy.orm import Session
from app.database import get_db
from app.middleware.auth_context import get_current_user, get_current_session
from app.schemas.account_schemas import AccountOverviewResponse
from app.services.account_overview_service import AccountOverviewService
from app.services.entitlement_service import EntitlementService
from app.common.correlation import get_correlation_id
from app.models.auth import UserIdentity, AuthSession


router = APIRouter(prefix="/accounts", tags=["accounts"])


@router.get("/overview", response_model=AccountOverviewResponse)
def get_account_overview(
    request: Request,
    profile_id: int = Query(..., description="Profile ID"),
    current_user: UserIdentity = Depends(get_current_user),
    current_session: AuthSession = Depends(get_current_session),
    db: Session = Depends(get_db)
):
    """Get account overview for a profile with partial-failure handling."""
    correlation_id = get_correlation_id(request)
    
    # Check profile access
    entitlement_service = EntitlementService(db)
    if not entitlement_service.check_profile_access(profile_id, current_user.id):
        raise HTTPException(status_code=403, detail="Access denied to this profile")
    
    # Get overview
    overview_service = AccountOverviewService(db)
    try:
        overview = overview_service.get_overview(profile_id)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    
    return AccountOverviewResponse(**overview)

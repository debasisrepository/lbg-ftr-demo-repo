"""Accounts router"""
import uuid

from fastapi import APIRouter, Depends, Request
from sqlalchemy.orm import Session

from app.core.errors import AuthorizationError
from app.core.security import decode_jwt_token
from app.database import get_db
from app.schemas.account_schemas import AccountsOverviewResponse, BankAccountOut, LoanSnapshotOut
from app.services.accounts_overview_service import AccountsOverviewService
from app.services.entitlement_service import EntitlementService
from app.services.profile_service import ProfileService

router = APIRouter(prefix="/accounts", tags=["accounts"])


def get_current_customer_and_profile(request: Request) -> tuple[uuid.UUID, uuid.UUID]:
    """Extract customer ID and active profile ID from JWT token"""
    auth_header = request.headers.get("Authorization")
    if not auth_header or not auth_header.startswith("Bearer "):
        raise AuthorizationError("Missing or invalid authorization header")

    token = auth_header.split(" ")[1]
    payload = decode_jwt_token(token)

    customer_id_str = payload.get("sub")
    if not customer_id_str:
        raise AuthorizationError("Invalid token: missing subject")

    profile_id_str = payload.get("active_profile_id")
    if not profile_id_str:
        raise AuthorizationError("Invalid token: no active profile")

    return uuid.UUID(customer_id_str), uuid.UUID(profile_id_str)


@router.get("/overview", response_model=AccountsOverviewResponse)
def get_accounts_overview(
    request: Request,
    db: Session = Depends(get_db)
):
    """Get accounts and loans overview for active profile"""
    customer_id, profile_id = get_current_customer_and_profile(request)

    # Check entitlement
    entitlement_service = EntitlementService()
    entitlement_service.require_capability(db, profile_id, "view_accounts")

    # Get accounts overview
    accounts_service = AccountsOverviewService()
    accounts_with_perm, loans = accounts_service.get_accounts_overview(
        db=db,
        customer_id=customer_id,
        profile_id=profile_id
    )

    # Convert to response DTOs
    account_outs = [
        BankAccountOut(
            bank_account_id=account.bank_account_id,
            external_account_ref=account.external_account_ref,
            account_type=account.account_type,
            account_name=account.account_name,
            sort_code_masked=account.sort_code_masked,
            account_number_masked=account.account_number_masked,
            currency_code=account.currency_code,
            account_holder_name=account.account_holder_name,
            current_balance_minor=account.current_balance_minor,
            available_balance_minor=account.available_balance_minor,
            overdraft_limit_minor=account.overdraft_limit_minor,
            freshness_at=account.freshness_at,
            source_status=account.source_status,
            payment_permission=payment_perm,
        )
        for account, payment_perm in accounts_with_perm
    ]

    loan_outs = [
        LoanSnapshotOut(
            loan_snapshot_id=loan.loan_snapshot_id,
            profile_id=loan.profile_id,
            external_loan_ref=loan.external_loan_ref,
            loan_name=loan.loan_name,
            outstanding_balance_minor=loan.outstanding_balance_minor,
            next_repayment_minor=loan.next_repayment_minor,
            next_repayment_date=loan.next_repayment_date,
            currency_code=loan.currency_code,
            freshness_at=loan.freshness_at,
            source_status=loan.source_status,
        )
        for loan in loans
    ]

    # Get profile display name
    profile_service = ProfileService()
    profile = profile_service.get_profile_by_id(db, profile_id)
    profile_display_name = profile.display_name if profile else "Unknown"

    return AccountsOverviewResponse(
        accounts=account_outs,
        loans=loan_outs,
        profile_id=profile_id,
        profile_display_name=profile_display_name,
    )

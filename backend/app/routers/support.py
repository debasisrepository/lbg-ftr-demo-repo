"""Support/scam claim endpoints"""
import uuid

from fastapi import APIRouter, Depends, HTTPException, Request
from sqlalchemy.orm import Session

from ..core.middleware import get_correlation_id
from ..database import get_db
from ..schemas.support_schemas import ScamClaimCreateRequest, ScamClaimResponse
from ..services.scam_claim_service import ScamClaimService

router = APIRouter()


def get_current_customer_id() -> uuid.UUID:
    """Stub: get customer ID from session"""
    return uuid.UUID("10000000-0000-0000-0000-000000000001")


@router.post("/scam-claims", response_model=ScamClaimResponse, status_code=201)
def create_scam_claim(
    request: Request,
    claim_request: ScamClaimCreateRequest,
    db: Session = Depends(get_db)
):
    """Create a new scam claim"""
    customer_id = get_current_customer_id()
    correlation_id = get_correlation_id(request)

    scam_claim_service = ScamClaimService(db)

    try:
        scam_claim = scam_claim_service.create_scam_claim(
            customer_id,
            claim_request.payment_order_id,
            claim_request.claim_reason_code,
            claim_request.notes,
            correlation_id
        )

        return ScamClaimResponse(
            scam_claim_id=scam_claim.scam_claim_id,
            claim_reference=scam_claim.claim_reference,
            claim_status=scam_claim.claim_status,
            claim_reason_code=scam_claim.claim_reason_code,
            reported_at=scam_claim.reported_at,
            support_case_reference=scam_claim.support_case_reference,
            fraud_case_reference=scam_claim.fraud_case_reference,
            payment_order_id=scam_claim.payment_order_id,
            created_at=scam_claim.created_at,
            updated_at=scam_claim.updated_at
        )
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/scam-claims/{claim_reference}", response_model=ScamClaimResponse, status_code=200)
def get_scam_claim(
    claim_reference: str,
    db: Session = Depends(get_db)
):
    """Get scam claim by reference"""
    scam_claim_service = ScamClaimService(db)

    try:
        scam_claim = scam_claim_service.get_scam_claim(claim_reference)

        return ScamClaimResponse(
            scam_claim_id=scam_claim.scam_claim_id,
            claim_reference=scam_claim.claim_reference,
            claim_status=scam_claim.claim_status,
            claim_reason_code=scam_claim.claim_reason_code,
            reported_at=scam_claim.reported_at,
            support_case_reference=scam_claim.support_case_reference,
            fraud_case_reference=scam_claim.fraud_case_reference,
            payment_order_id=scam_claim.payment_order_id,
            created_at=scam_claim.created_at,
            updated_at=scam_claim.updated_at
        )
    except Exception as e:
        raise HTTPException(status_code=404, detail=str(e))

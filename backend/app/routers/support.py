"""Support/scam claim endpoints"""
import uuid

from fastapi import APIRouter, Depends, HTTPException, Request
from sqlalchemy.orm import Session

from ..core.auth_middleware import get_current_customer_id
from ..core.middleware import get_correlation_id
from ..database import get_db
from ..schemas.support_schemas import ScamClaimCreateRequest, ScamClaimResponse
from ..services.scam_claim_service import ScamClaimService

router = APIRouter()


@router.post("/scam-claims", response_model=ScamClaimResponse, status_code=201)
def create_scam_claim(
    request: Request,
    claim_request: ScamClaimCreateRequest,
    customer_id: uuid.UUID = Depends(get_current_customer_id),
    db: Session = Depends(get_db)
):
    """Create a new scam claim"""
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
            customer_id=scam_claim.customer_id,
            claim_reference=scam_claim.claim_reference,
            claim_status=scam_claim.claim_status,
            claim_reason_code=scam_claim.claim_reason_code,
            reported_at=scam_claim.reported_at,
            support_case_reference=scam_claim.support_case_reference,
            fraud_case_reference=scam_claim.fraud_case_reference,
            payment_order_id=scam_claim.payment_order_id,
            reimbursement_timeline_days=scam_claim_service.get_reimbursement_timeline_days(claim_request.claim_reason_code),
            created_at=scam_claim.created_at,
            updated_at=scam_claim.updated_at
        )
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/scam-claims/{claim_reference}", response_model=ScamClaimResponse, status_code=200)
def get_scam_claim(
    claim_reference: str,
    customer_id: uuid.UUID = Depends(get_current_customer_id),
    db: Session = Depends(get_db)
):
    """Get scam claim by reference"""
    scam_claim_service = ScamClaimService(db)

    try:
        scam_claim = scam_claim_service.get_scam_claim(claim_reference)
        
        # Verify ownership
        if scam_claim.customer_id != customer_id:
            raise HTTPException(status_code=404, detail="Scam claim not found")

        return ScamClaimResponse(
            scam_claim_id=scam_claim.scam_claim_id,
            customer_id=scam_claim.customer_id,
            claim_reference=scam_claim.claim_reference,
            claim_status=scam_claim.claim_status,
            claim_reason_code=scam_claim.claim_reason_code,
            reported_at=scam_claim.reported_at,
            support_case_reference=scam_claim.support_case_reference,
            fraud_case_reference=scam_claim.fraud_case_reference,
            payment_order_id=scam_claim.payment_order_id,
            reimbursement_timeline_days=scam_claim_service.get_reimbursement_timeline_days(scam_claim.claim_reason_code or "other"),
            created_at=scam_claim.created_at,
            updated_at=scam_claim.updated_at
        )
    except Exception as e:
        raise HTTPException(status_code=404, detail=str(e))

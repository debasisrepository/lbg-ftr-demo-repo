from fastapi import APIRouter, Depends, Request, status
from sqlalchemy.orm import Session
from app.database import get_db
from app.schemas.sca_schemas import StepUpVerifyRequest, StepUpVerifyResponse
from app.services.sca_service import SCAService
from app.common.correlation import get_correlation_id


router = APIRouter(prefix="/sca", tags=["Step-up Authentication"])


@router.post("/verify-step-up", response_model=StepUpVerifyResponse, status_code=status.HTTP_200_OK)
async def verify_step_up(
    request: Request,
    verify_data: StepUpVerifyRequest,
    db: Session = Depends(get_db)
):
    """
    Verify step-up authentication (passcode or biometric).
    
    Supports:
    - Passcode: 6-digit code verification
    - Biometric: biometric assertion verification
    
    Returns verification result with remaining attempts.
    After 3 failed passcode attempts, passcode is locked and user must return to password login.
    """
    correlation_id = get_correlation_id(request)
    
    sca_service = SCAService(db, correlation_id)
    
    result = await sca_service.verify_step_up(
        session_id=verify_data.session_id,
        method=verify_data.method,
        passcode=verify_data.passcode,
        biometric_assertion=verify_data.biometric_assertion,
        device_id=verify_data.device_id
    )
    
    return StepUpVerifyResponse(**result)

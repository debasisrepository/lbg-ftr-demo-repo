from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from app.database import get_db
from app.auth.deps import get_current_user
from app.auth.models import AppUser
from app.api.my_cases.schemas import (
    CreateCaseRequest, CaseResponse, CaseListResponse,
    CaseListItem, CaseDetailResponse
)
from app.services.case.service import CaseService
from uuid import UUID


router = APIRouter()


@router.post("/cases", response_model=CaseResponse, tags=["cases"])
def create_case(
    payload: CreateCaseRequest,
    current_user: AppUser = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Create Case from app entry point"""
    case_service = CaseService(db)
    
    from app.services.case.schemas import CreateCaseRequest as ServiceRequest
    request = ServiceRequest(
        origin_source=payload.origin_source,
        problem_statement=payload.problem_statement
    )
    
    case = case_service.create_case(current_user.id, request)
    db.commit()
    
    return case


@router.get("/cases", response_model=CaseListResponse, tags=["cases"])
def list_cases(
    limit: int = Query(50, ge=1, le=100),
    offset: int = Query(0, ge=0),
    current_user: AppUser = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """List customer's Cases with pagination"""
    case_service = CaseService(db)
    
    result = case_service.list_customer_cases(current_user.id, limit, offset)
    
    items = [
        CaseListItem(
            id=case.id,
            case_ref=case.case_ref,
            status=case.status,
            classification=case.classification,
            owner_team_display=case.owner_team_display,
            last_update_at=case.last_update_at,
            expected_by_at=case.expected_by_at
        )
        for case in result["items"]
    ]
    
    return CaseListResponse(
        items=items,
        total=result["total"]
    )


@router.get("/cases/{case_id}", response_model=CaseDetailResponse, tags=["cases"])
def get_case(
    case_id: UUID,
    current_user: AppUser = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get Case detail"""
    case_service = CaseService(db)
    
    case = case_service.get_case(case_id)
    if not case:
        raise HTTPException(status_code=404, detail="Case not found")
    
    if case.customer_user_id != current_user.id:
        raise HTTPException(status_code=403, detail="Not your case")
    
    return CaseDetailResponse(
        id=case.id,
        case_ref=case.case_ref,
        customer_user_id=case.customer_user_id,
        status=case.status,
        problem_statement=case.problem_statement,
        classification=case.classification,
        owner_team_display=case.owner_team_display,
        owner_colleague_display=case.owner_colleague_display,
        route_reason=case.route_reason,
        expected_by_at=case.expected_by_at,
        last_update_at=case.last_update_at,
        created_at=case.created_at
    )

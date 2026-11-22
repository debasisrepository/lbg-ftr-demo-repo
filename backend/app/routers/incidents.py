"""Incident reporting router (BR-OPS-008)"""
import uuid

from fastapi import APIRouter, Depends, HTTPException, Request, status
from sqlalchemy.orm import Session

from ..core.errors import AuthorizationError, ValidationError
from ..core.security import decode_jwt_token
from ..database import get_db
from ..schemas.incident_schemas import (
    IncidentReportCreateRequest,
    IncidentReportResponse,
)
from ..services.incident_report_service import IncidentReportService

router = APIRouter(prefix="/incidents", tags=["incidents"])


def get_current_customer_id(request: Request) -> uuid.UUID:
    """Extract customer ID from JWT token"""
    auth_header = request.headers.get("Authorization")
    if not auth_header or not auth_header.startswith("Bearer "):
        raise AuthorizationError("Missing or invalid authorization header")

    token = auth_header.split(" ")[1]
    payload = decode_jwt_token(token)

    customer_id_str = payload.get("sub")
    if not customer_id_str:
        raise AuthorizationError("Invalid token: missing subject")

    return uuid.UUID(customer_id_str)


def get_correlation_id() -> str:
    """Generate correlation ID for tracing"""
    return f"corr_{uuid.uuid4().hex[:16]}"


@router.post("", response_model=IncidentReportResponse, status_code=status.HTTP_201_CREATED)
def create_incident_report(
    request: IncidentReportCreateRequest,
    customer_id: uuid.UUID = Depends(get_current_customer_id),
    db: Session = Depends(get_db),
) -> IncidentReportResponse:
    """Create a new incident report (BR-OPS-008)"""
    try:
        incident_service = IncidentReportService(db)
        incident_report = incident_service.create_incident_report(
            customer_id=customer_id,
            incident_category=request.incident_category,
            incident_title=request.incident_title,
            incident_description=request.incident_description,
            severity=request.severity,
            correlation_id=get_correlation_id()
        )
        db.commit()
        return IncidentReportResponse.model_validate(incident_report)
    except ValidationError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))


@router.get("/{incident_reference}", response_model=IncidentReportResponse)
def get_incident_report(
    incident_reference: str,
    customer_id: uuid.UUID = Depends(get_current_customer_id),
    db: Session = Depends(get_db),
) -> IncidentReportResponse:
    """Get incident report by reference (BR-OPS-008)"""
    try:
        incident_service = IncidentReportService(db)
        # H-003: Check ownership at service/DB level, not after loading
        incident_report = incident_service.get_incident_report_for_customer(incident_reference, customer_id)
        return IncidentReportResponse.model_validate(incident_report)
    except ValidationError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))


@router.get("", response_model=list[IncidentReportResponse])
def list_incident_reports(
    customer_id: uuid.UUID = Depends(get_current_customer_id),
    db: Session = Depends(get_db),
) -> list[IncidentReportResponse]:
    """List incident reports for the current customer (BR-OPS-008)"""
    incident_service = IncidentReportService(db)
    incident_reports = incident_service.list_customer_incidents(customer_id)
    return [IncidentReportResponse.model_validate(ir) for ir in incident_reports]

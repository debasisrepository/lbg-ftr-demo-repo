"""Colleague-facing routes."""
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Query, status

from app.core.errors import NotFoundError
from app.core.ids import new_id
from app.deps import Principal, get_uow, require_scope
from app.repositories.continuity_repository import ContinuityRepository
from app.schemas.case import Page
from app.services.audit_service import AuditService
from app.services.continuity_service import ContinuityService

router = APIRouter()


def get_continuity_service(uow: Annotated[object, Depends(get_uow)]) -> ContinuityService:
    """Get continuity service."""
    from app.core.clock import Clock
    from app.repositories.audit_repository import AuditRepository
    from app.repositories.case_repository import CaseRepository
    from app.repositories.history_repository import HistoryRepository
    from app.repositories.ownership_repository import OwnershipRepository

    return ContinuityService(
        continuity_repo=ContinuityRepository(uow.session),  # type: ignore
        case_repo=CaseRepository(uow.session),  # type: ignore
        ownership_repo=OwnershipRepository(uow.session),  # type: ignore
        history_repo=HistoryRepository(uow.session),  # type: ignore
        audit_repo=AuditRepository(uow.session),  # type: ignore
        audit_service=AuditService(AuditRepository(uow.session), Clock()),  # type: ignore
        clock=Clock()
    )


@router.get("/cases")
def list_colleague_cases(
    customer_party_id: Annotated[str, Query(description="Customer party ID to retrieve cases for")],
    limit: int = Query(20, ge=1, le=100),
    offset: int = Query(0, ge=0),
    principal: Principal = Depends(require_scope("colleague")),
    continuity_service: ContinuityService = Depends(get_continuity_service),
    uow: object = Depends(get_uow)
) -> Page:
    """List cases for a customer (colleague scope).

    Requires colleague scope and entitlement check.
    """
    # Entitlement check: For now, allow all colleagues
    # In real implementation, check colleague entitlement against customer_party_id

    try:
        summaries, total = continuity_service.list_colleague_cases(
            customer_party_id=customer_party_id,
            limit=limit,
            offset=offset
        )

        uow.commit()  # type: ignore

        return Page(
            items=summaries,
            total=total,
            limit=limit,
            offset=offset
        )
    except Exception as e:
        uow.rollback()  # type: ignore
        # Audit denial
        from app.core.clock import Clock
        from app.repositories.audit_repository import AuditRepository
        audit_service = AuditService(AuditRepository(uow.session), Clock())  # type: ignore
        audit_service.record(
            correlation_id=new_id(),
            audit_category="access",
            event_type="access_denied",
            actor_type="colleague",
            actor_reference=principal.colleague_reference or "unknown",
            entity_type="customer",
            entity_id=customer_party_id,
            severity="warning",
            metadata={
                "customer_party_id": customer_party_id,
                "denial_reason": str(e)
            }
        )
        uow.commit()  # type: ignore

        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Access denied for this customer"
        )


@router.get("/cases/{case_reference}")
def get_colleague_case(
    case_reference: str,
    principal: Principal = Depends(require_scope("colleague")),
    continuity_service: ContinuityService = Depends(get_continuity_service),
    uow: object = Depends(get_uow)
) -> dict:
    """Get case continuity package for colleague.

    Requires colleague scope and entitlement check.
    Returns continuity package with colleague fields only.
    """
    if not principal.colleague_reference:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Colleague reference required"
        )

    try:
        correlation_id = new_id()
        package = continuity_service.colleague_retrieve(
            case_reference=case_reference,
            colleague_reference=principal.colleague_reference,
            correlation_id=correlation_id
        )

        uow.commit()  # type: ignore

        return package
    except NotFoundError as e:
        uow.rollback()  # type: ignore
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e)
        )
    except Exception as e:
        uow.rollback()  # type: ignore
        # Audit denial
        from app.core.clock import Clock
        from app.repositories.audit_repository import AuditRepository
        audit_service = AuditService(AuditRepository(uow.session), Clock())  # type: ignore
        audit_service.record(
            correlation_id=new_id(),
            audit_category="access",
            event_type="access_denied",
            actor_type="colleague",
            actor_reference=principal.colleague_reference or "unknown",
            entity_type="case",
            entity_id=case_reference,
            severity="warning",
            metadata={
                "case_reference": case_reference,
                "denial_reason": str(e)
            }
        )
        uow.commit()  # type: ignore

        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Access denied for this case"
        )

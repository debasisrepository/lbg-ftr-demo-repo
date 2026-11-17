"""Case repository."""
from uuid import UUID

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.models.case import Case, CaseAnchorLink, CaseStatusProjection


class CaseRepository:
    """Repository for case operations."""

    def __init__(self, session: Session):
        self.session = session

    def get_by_reference(self, case_reference: str) -> Case | None:
        """Get a case by reference (no customer scoping)."""
        stmt = select(Case).where(Case.case_reference == case_reference)
        return self.session.scalars(stmt).first()
    
    def get_by_reference_for_customer(self, case_reference: str, customer_party_id: str) -> Case | None:
        """Get a case by reference for a specific customer."""
        stmt = select(Case).where(
            Case.case_reference == case_reference,
            Case.customer_party_id == customer_party_id
        )
        return self.session.scalars(stmt).first()

    def list_for_customer(
        self,
        customer_party_id: str,
        lifecycle_state: str | None = None,
        include_closed: bool = True,
        limit: int = 20,
        offset: int = 0
    ) -> tuple[list[Case], int]:
        """List cases for a customer with optional filtering."""
        stmt = select(Case).where(Case.customer_party_id == customer_party_id)
        
        if lifecycle_state:
            stmt = stmt.where(Case.current_lifecycle_state == lifecycle_state)
        
        if not include_closed:
            stmt = stmt.where(Case.closed_at.is_(None))
        
        # Count total
        count_stmt = select(func.count()).select_from(stmt.subquery())
        total = self.session.scalar(count_stmt) or 0
        
        # Apply sorting and pagination
        stmt = stmt.order_by(
            Case.latest_meaningful_update_at.desc().nulls_last(),
            Case.opened_at.desc()
        ).limit(limit).offset(offset)
        
        cases = list(self.session.scalars(stmt))
        return cases, total

    def find_open_by_issue_type(self, customer_party_id: str, issue_type: str) -> Case | None:
        """Find an open case for a customer with a specific issue type."""
        stmt = select(Case).where(
            Case.customer_party_id == customer_party_id,
            Case.issue_type == issue_type,
            Case.closed_at.is_(None)
        )
        return self.session.scalars(stmt).first()

    def create(self, case: Case) -> Case:
        """Create a new case."""
        self.session.add(case)
        self.session.flush()
        return case

    def create_anchor_link(self, anchor_link: CaseAnchorLink) -> CaseAnchorLink:
        """Create a case anchor link."""
        self.session.add(anchor_link)
        self.session.flush()
        return anchor_link

    def create_status_projection(self, projection: CaseStatusProjection) -> CaseStatusProjection:
        """Create a case status projection."""
        self.session.add(projection)
        self.session.flush()
        return projection

    def current_projection(self, case_id: UUID) -> CaseStatusProjection | None:
        """Get the current status projection for a case."""
        stmt = select(CaseStatusProjection).where(
            CaseStatusProjection.case_id == case_id,
            CaseStatusProjection.is_current == True  # noqa: E712
        )
        return self.session.scalars(stmt).first()

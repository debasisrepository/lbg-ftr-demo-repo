"""Ownership repository."""
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.ownership import CaseOwnership, ExpectedByCommitment


class OwnershipRepository:
    """Repository for case ownership and expected-by commitments."""

    def __init__(self, session: Session):
        self.session = session

    def current_ownership(self, case_id: UUID) -> CaseOwnership | None:
        """Get the current ownership record for a case."""
        stmt = select(CaseOwnership).where(
            CaseOwnership.case_id == case_id,
            CaseOwnership.is_current == True  # noqa: E712
        )
        return self.session.scalars(stmt).first()

    def current_expected_by(self, case_id: UUID) -> ExpectedByCommitment | None:
        """Get the current expected-by commitment for a case."""
        stmt = select(ExpectedByCommitment).where(
            ExpectedByCommitment.case_id == case_id,
            ExpectedByCommitment.is_current == True  # noqa: E712
        )
        return self.session.scalars(stmt).first()

    def insert_ownership(self, ownership: CaseOwnership) -> CaseOwnership:
        """Insert a new ownership record."""
        self.session.add(ownership)
        self.session.flush()
        return ownership

    def insert_expected_by(self, expected_by: ExpectedByCommitment) -> ExpectedByCommitment:
        """Insert a new expected-by commitment."""
        self.session.add(expected_by)
        self.session.flush()
        return expected_by

    def active_mapping(self, owner_team_code: str):
        """Get the active owner team mapping for a given code."""
        from app.models.config import OwnerTeamMapping

        stmt = select(OwnerTeamMapping).where(
            OwnerTeamMapping.owner_team_code == owner_team_code,
            OwnerTeamMapping.is_active == True  # noqa: E712
        )
        return self.session.scalars(stmt).first()

    def close_current_and_insert_ownership(
        self,
        case_id: UUID,
        new_ownership: CaseOwnership,
        effective_to
    ) -> CaseOwnership:
        """Close current ownership and insert new one."""
        current = self.current_ownership(case_id)
        if current:
            current.effective_to = effective_to
            current.is_current = False
            self.session.flush()

        self.session.add(new_ownership)
        self.session.flush()
        return new_ownership

    def close_current_and_insert_expected_by(
        self,
        case_id: UUID,
        new_expected_by: ExpectedByCommitment,
        effective_to
    ) -> ExpectedByCommitment:
        """Close current expected-by and insert new one."""
        current = self.current_expected_by(case_id)
        if current:
            current.effective_to = effective_to
            current.is_current = False
            self.session.flush()

        self.session.add(new_expected_by)
        self.session.flush()
        return new_expected_by

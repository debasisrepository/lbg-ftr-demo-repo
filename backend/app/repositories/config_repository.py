"""Configuration repository."""
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.config import CaseLifecycleTransition, IssueEligibilityRule, OwnerTeamMapping


class ConfigRepository:
    """Repository for configuration data."""

    def __init__(self, session: Session):
        self.session = session

    def active_rule(self, issue_type: str) -> IssueEligibilityRule | None:
        """Get the active eligibility rule for an issue type."""
        stmt = select(IssueEligibilityRule).where(
            IssueEligibilityRule.issue_type == issue_type
        )
        return self.session.scalars(stmt).first()

    def active_owner_mapping(self, owner_team_code: str) -> OwnerTeamMapping | None:
        """Get the active owner team mapping."""
        stmt = select(OwnerTeamMapping).where(
            OwnerTeamMapping.owner_team_code == owner_team_code,
            OwnerTeamMapping.is_active == True  # noqa: E712
        )
        return self.session.scalars(stmt).first()
    
    def active_transitions(self) -> list[CaseLifecycleTransition]:
        """Get all active lifecycle transitions."""
        stmt = select(CaseLifecycleTransition).where(
            CaseLifecycleTransition.is_active == True  # noqa: E712
        )
        return list(self.session.scalars(stmt).all())

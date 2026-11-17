"""Policy service."""
from dataclasses import dataclass

from app.repositories.config_repository import ConfigRepository


@dataclass
class PolicyResult:
    """Result of a policy decision."""
    outcome: str  # "allow" or "deny"
    denial_reason_code: str | None = None
    metadata: dict | None = None


class PolicyService:
    """Service for policy decisions."""
    
    def __init__(self, config_repo: ConfigRepository):
        self.config_repo = config_repo
    
    def decide(
        self,
        scope: str,
        issue_type: str | None = None,
        customer_party_id: str | None = None
    ) -> PolicyResult:
        """Make a deterministic policy decision.
        
        Args:
            scope: Decision scope (e.g., "eligibility", "continuity_release")
            issue_type: Issue type for eligibility decisions
            customer_party_id: Customer ID for access decisions
        
        Returns:
            PolicyResult with outcome and optional denial reason
        """
        if scope == "eligibility":
            return self._decide_eligibility(issue_type)
        
        # Default allow for other scopes in this tier
        return PolicyResult(outcome="allow")
    
    def _decide_eligibility(self, issue_type: str | None) -> PolicyResult:
        """Decide if an issue type is eligible for case creation."""
        if not issue_type:
            return PolicyResult(
                outcome="deny",
                denial_reason_code="missing_issue_type"
            )
        
        rule = self.config_repo.active_rule(issue_type)
        
        if not rule:
            # No rule found: treat as not eligible
            return PolicyResult(
                outcome="deny",
                denial_reason_code="no_eligibility_rule",
                metadata={"issue_type": issue_type}
            )
        
        if not rule.is_eligible:
            return PolicyResult(
                outcome="deny",
                denial_reason_code="issue_type_not_eligible",
                metadata={
                    "issue_type": issue_type,
                    "redirect_journey_code": rule.redirect_journey_code
                }
            )
        
        return PolicyResult(outcome="allow")

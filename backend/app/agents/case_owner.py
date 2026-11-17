"""Case Owner Agent - drafts hand-off summaries and heartbeat updates."""
import uuid
from dataclasses import dataclass


@dataclass
class SummaryDraft:
    """Hand-off summary draft."""
    summary_text: str
    summary_type: str  # 'handoff_pack' or 'interim'


@dataclass
class CustomerUpdateDraft:
    """Customer heartbeat update draft."""
    update_text: str


class CaseOwnerAgent:
    """
    Case Owner Agent (one per active Case).
    Drafts hand-off summaries and heartbeat updates.
    Max autonomy L1.
    """
    agent_code = "case_owner_agent"
    
    def compose_summary(
        self,
        problem_statement: str,
        classification: str,
        route_reason: str,
        evidence_count: int
    ) -> SummaryDraft:
        """
        Compose hand-off summary for colleague view.
        
        For demo: deterministic template.
        In production: LLM-assisted with ResultValidator.
        
        Args:
            problem_statement: Customer's problem statement
            classification: Issue classification
            route_reason: Why routed to colleague
            evidence_count: Number of evidence items
        
        Returns:
            SummaryDraft
        """
        # Deterministic template (SummaryTemplate fallback)
        summary_text = (
            f"Customer reports: {problem_statement[:200]}. "
            f"Classified as {classification}. "
            f"Route reason: {route_reason}. "
            f"Evidence items: {evidence_count}."
        )
        
        return SummaryDraft(
            summary_text=summary_text[:1500],  # Max 1500 chars
            summary_type="handoff_pack"
        )
    
    def draft_customer_update(
        self,
        case_ref: str,
        status: str,
        expected_by: str
    ) -> CustomerUpdateDraft:
        """
        Draft plain-English heartbeat update for customer.
        
        Args:
            case_ref: Case reference
            status: Current status
            expected_by: Expected by time
        
        Returns:
            CustomerUpdateDraft
        """
        # Deterministic template
        update_text = (
            f"We're still working on your case {case_ref}. "
            f"A colleague will update you by {expected_by}."
        )
        
        return CustomerUpdateDraft(
            update_text=update_text[:400]  # Max 400 chars
        )

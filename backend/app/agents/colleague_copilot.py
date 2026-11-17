"""Colleague Copilot Agent - one-screen summary assistance."""
from dataclasses import dataclass


@dataclass
class CopilotNote:
    """One-screen summary note for colleague."""
    note_text: str


class ColleagueCopilotAgent:
    """
    Colleague Copilot Agent provides next-best context for colleagues.
    Max autonomy L0 (assistance only, no actions).
    Runs under 1.5s budget, failure does not block handoff pack.
    """
    agent_code = "colleague_copilot_agent"
    
    def next_best_context(
        self,
        summary_text: str,
        classification: str,
        route_reason: str,
        vulnerability_flag: bool
    ) -> CopilotNote:
        """
        Generate next-best context note for colleague.
        
        For demo: deterministic template.
        In production: LLM-assisted under 1.5s budget.
        
        Args:
            summary_text: Hand-off summary
            classification: Issue classification
            route_reason: Route reason
            vulnerability_flag: Vulnerability indicator present
        
        Returns:
            CopilotNote
        """
        # Deterministic template
        note_parts = [f"Classification: {classification}"]
        
        if vulnerability_flag:
            note_parts.append("⚠️ Vulnerability indicators present")
        
        note_parts.append(f"Routed because: {route_reason}")
        note_parts.append("Review evidence and transcript before replying.")
        
        note_text = ". ".join(note_parts)
        
        return CopilotNote(
            note_text=note_text[:1000]  # Max 1000 chars
        )

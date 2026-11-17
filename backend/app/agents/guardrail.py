from dataclasses import dataclass


@dataclass
class GuardrailResult:
    """Result from guardrail screening"""
    triggers: list[str]
    force_human: bool
    reasoning: str


class GuardrailSupervisorAgent:
    """Guardrail Supervisor agent - screens for escalation triggers"""
    
    def __init__(self):
        self.agent_code = "guardrail_supervisor_agent"
    
    def screen(self, customer_text: str, context: dict) -> GuardrailResult:
        """
        Screen for seven escalation triggers:
        1. Low confidence
        2. Vulnerability indicators
        3. Distress signals
        4. Scam-in-progress
        5. Complaint language
        6. Repeated failure
        7. Explicit human request
        """
        triggers = []
        lower_text = customer_text.lower()
        
        # Check for triggers
        if context.get('confidence_pct', 100) < 70:
            triggers.append("low_confidence")
        
        if any(word in lower_text for word in ['vulnerable', 'disabled', 'elderly']):
            triggers.append("vulnerability")
        
        if any(word in lower_text for word in ['distress', 'anxious', 'worried', 'scared']):
            triggers.append("distress")
        
        if any(word in lower_text for word in ['scam', 'fraud', 'stolen']):
            triggers.append("scam_in_progress")
        
        if any(word in lower_text for word in ['complaint', 'complain']):
            triggers.append("complaint")
        
        if context.get('repeated_failure', False):
            triggers.append("repeated_failure")
        
        if any(word in lower_text for word in ['human', 'person', 'speak to someone', 'talk to someone']):
            triggers.append("explicit_human_request")
        
        force_human = len(triggers) > 0
        reasoning = f"Detected triggers: {', '.join(triggers)}" if triggers else "No escalation triggers"
        
        return GuardrailResult(
            triggers=triggers,
            force_human=force_human,
            reasoning=reasoning
        )

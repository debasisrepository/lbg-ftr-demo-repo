from app.agents.base import BaseAgent, AgentResult


class IntakeTriageAgent(BaseAgent):
    """Intake and Triage agent - classifies customer issues"""
    
    def __init__(self):
        super().__init__("intake_triage_agent", max_autonomy_level=1)
    
    def process(self, customer_text: str, context: dict) -> AgentResult:
        """
        Classify customer issue and determine if in scope for assistant resolution
        For demo: use heuristic classification
        """
        lower_text = customer_text.lower()
        
        # Simple heuristic classification
        if any(word in lower_text for word in ['fraud', 'scam', 'stolen']):
            classification = "fraud_report"
            in_scope = False
        elif any(word in lower_text for word in ['complaint', 'complain', 'unhappy']):
            classification = "complaint"
            in_scope = False
        elif any(word in lower_text for word in ['human', 'person', 'speak to someone']):
            classification = "general_query"
            in_scope = False
        elif any(word in lower_text for word in ['payment', 'transaction', 'charge']):
            classification = "payment_query"
            in_scope = True
        elif any(word in lower_text for word in ['card', 'declined']):
            classification = "card_declined"
            in_scope = True
        else:
            classification = "general_query"
            in_scope = True
        
        return AgentResult(
            classification=classification,
            in_scope=in_scope,
            confidence_pct=75,
            reasoning_summary=f"Classified as {classification} based on keywords",
            proposed_action="create_case" if not in_scope else "provide_information",
            next_question=None
        )

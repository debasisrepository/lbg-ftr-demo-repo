from abc import ABC, abstractmethod
from dataclasses import dataclass


@dataclass
class AgentResult:
    """Result from agent reasoning"""
    classification: str | None
    in_scope: bool
    confidence_pct: int
    reasoning_summary: str
    proposed_action: str | None
    next_question: str | None


class BaseAgent(ABC):
    """Base class for all agents"""
    
    def __init__(self, agent_code: str, max_autonomy_level: int):
        self.agent_code = agent_code
        self.max_autonomy_level = max_autonomy_level
    
    @abstractmethod
    def process(self, customer_text: str, context: dict) -> AgentResult:
        """Process customer input and return agent decision"""
        pass

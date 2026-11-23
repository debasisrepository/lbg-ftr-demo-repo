"""
ScamCheckRepository - persistence for scam check outcomes.
Requirement: REQ-PAY-006, REQ-PAY-007
"""
import uuid
from datetime import datetime

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.scam_check_outcome import ScamCheckOutcome


class ScamCheckRepository:
    """Repository for scam check outcome persistence."""
    
    def __init__(self, db: Session):
        self.db = db
    
    def create(self, outcome: ScamCheckOutcome) -> ScamCheckOutcome:
        """
        Create a new scam check outcome.
        
        Args:
            outcome: ScamCheckOutcome to persist
        
        Returns:
            Created ScamCheckOutcome
        """
        self.db.add(outcome)
        self.db.flush()
        self.db.refresh(outcome)
        return outcome
    
    def get_by_payment_and_version(
        self,
        payment_intent_id: uuid.UUID,
        review_version: int
    ) -> ScamCheckOutcome | None:
        """
        Get scam check outcome by payment and review version.
        
        Args:
            payment_intent_id: Payment intent ID
            review_version: Review version
        
        Returns:
            ScamCheckOutcome or None
        """
        stmt = select(ScamCheckOutcome).where(
            ScamCheckOutcome.payment_intent_id == payment_intent_id,
            ScamCheckOutcome.review_version == review_version
        )
        return self.db.execute(stmt).scalar_one_or_none()
    
    def update_customer_decision(
        self,
        outcome: ScamCheckOutcome,
        decision: str,
        decision_at: datetime
    ) -> ScamCheckOutcome:
        """
        Update customer warning decision.
        
        Args:
            outcome: ScamCheckOutcome to update
            decision: Customer decision ('stopped' or 'continued')
            decision_at: When decision was made
        
        Returns:
            Updated ScamCheckOutcome
        """
        outcome.customer_decision = decision
        outcome.customer_decision_at = decision_at
        outcome.updated_at = datetime.now(datetime.now().astimezone().tzinfo)
        self.db.flush()
        self.db.refresh(outcome)
        return outcome

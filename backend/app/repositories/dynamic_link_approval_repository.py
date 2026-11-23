"""
DynamicLinkApprovalRepository - repository for dynamic link approval records.
Requirement: FR-PAY-007, FR-PAY-008
"""
import uuid

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.dynamic_link_approval import DynamicLinkApproval


class DynamicLinkApprovalRepository:
    """Repository for dynamic link approval operations."""
    
    def __init__(self, db: Session):
        self.db = db
    
    def create(self, approval: DynamicLinkApproval) -> DynamicLinkApproval:
        """
        Create a new dynamic link approval record.
        
        Args:
            approval: DynamicLinkApproval instance
        
        Returns:
            Created DynamicLinkApproval
        """
        self.db.add(approval)
        self.db.flush()
        return approval
    
    def get_successful_approval(
        self,
        payment_intent_id: uuid.UUID,
        review_version: int,
        review_fingerprint: str
    ) -> DynamicLinkApproval | None:
        """
        Get successful approval for payment intent, review version and fingerprint.
        
        Args:
            payment_intent_id: Payment intent ID
            review_version: Review version
            review_fingerprint: Review fingerprint
        
        Returns:
            DynamicLinkApproval if found and successful, None otherwise
        """
        stmt = select(DynamicLinkApproval).where(
            DynamicLinkApproval.payment_intent_id == payment_intent_id,
            DynamicLinkApproval.review_version == review_version,
            DynamicLinkApproval.review_fingerprint == review_fingerprint,
            DynamicLinkApproval.approval_outcome == "success"
        )
        return self.db.execute(stmt).scalar_one_or_none()

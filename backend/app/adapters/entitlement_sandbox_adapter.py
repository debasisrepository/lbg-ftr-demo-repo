"""
Entitlement sandbox adapter for checking resource access permissions.
In production, this would call the Customer Access Entitlement service.
Requirement: REQ-AUTH-002
"""
import uuid

from sqlalchemy import and_, select
from sqlalchemy.orm import Session

from app.models.sandbox_entitlement import SandboxEntitlement


class EntitlementSandboxAdapter:
    """Sandbox adapter for entitlement checks using seeded sandbox_entitlements."""
    
    def __init__(self, db: Session):
        self.db = db
    
    def check_resource_access(
        self,
        customer_id: uuid.UUID,
        resource_type: str,
        resource_reference: str,
        entitlement_type: str | None = None
    ) -> str:
        """
        Check if customer has access to a specific resource.
        
        Args:
            customer_id: Customer profile reference ID
            resource_type: Type of resource (account, payee, payment)
            resource_reference: Specific resource ID or '*' for all
            entitlement_type: Optional filter for 'view', 'pay', or 'approve' (Release 2)
        
        Returns:
            Decision: 'allow', 'deny', or 'conditional'
        """
        # Check for wildcard entitlement first
        stmt = select(SandboxEntitlement).where(
            and_(
                SandboxEntitlement.customer_profile_ref_id == customer_id,
                SandboxEntitlement.resource_type == resource_type,
                SandboxEntitlement.resource_reference == "*"
            )
        )
        
        # Release 2: Filter by entitlement_type if specified (BR-PAY-012)
        if entitlement_type:
            stmt = stmt.where(SandboxEntitlement.entitlement_type == entitlement_type)
        
        wildcard = self.db.execute(stmt).scalar_one_or_none()
        
        if wildcard:
            return wildcard.decision
        
        # Check for specific resource entitlement
        stmt = select(SandboxEntitlement).where(
            and_(
                SandboxEntitlement.customer_profile_ref_id == customer_id,
                SandboxEntitlement.resource_type == resource_type,
                SandboxEntitlement.resource_reference == resource_reference
            )
        )
        
        # Release 2: Filter by entitlement_type if specified
        if entitlement_type:
            stmt = stmt.where(SandboxEntitlement.entitlement_type == entitlement_type)
        
        specific = self.db.execute(stmt).scalar_one_or_none()
        
        if specific:
            return specific.decision
        
        # Default to deny if no entitlement found
        return "deny"
    
    def get_customer_entitlements(
        self,
        customer_id: uuid.UUID,
        resource_type: str | None = None
    ) -> list[SandboxEntitlement]:
        """
        Get all entitlements for a customer, optionally filtered by resource type.
        
        Args:
            customer_id: Customer profile reference ID
            resource_type: Optional resource type filter
        
        Returns:
            List of entitlement records
        """
        stmt = select(SandboxEntitlement).where(
            SandboxEntitlement.customer_profile_ref_id == customer_id
        )
        
        if resource_type:
            stmt = stmt.where(SandboxEntitlement.resource_type == resource_type)
        
        result = self.db.execute(stmt)
        return list(result.scalars().all())

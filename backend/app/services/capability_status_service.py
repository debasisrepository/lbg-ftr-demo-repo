"""
Capability status service.
Requirement: FR-ACCT-001, FR-ACCT-003, FR-PAY-001, FR-PAY-011
"""

from sqlalchemy.orm import Session

from app.models.capability_status_record import CapabilityStatusRecord
from app.repositories.capability_status_repository import CapabilityStatusRepository


class CapabilityStatusService:
    """Service for capability status operations."""
    
    def __init__(
        self,
        db: Session,
        capability_repo: CapabilityStatusRepository | None = None
    ):
        self.db = db
        self.capability_repo = capability_repo or CapabilityStatusRepository(db)
    
    def get_capability_status(self, capability_name: str) -> CapabilityStatusRecord | None:
        """
        Get current status for a capability.
        
        Args:
            capability_name: Capability identifier
        
        Returns:
            Current capability status or None
        """
        return self.capability_repo.get_current_status(capability_name)
    
    def get_all_capability_statuses(self) -> list[CapabilityStatusRecord]:
        """Get all current capability statuses (4 total)."""
        return self.capability_repo.get_all_current_statuses()

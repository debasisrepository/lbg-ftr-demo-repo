"""
Payee service for saved payees.
Requirement: FR-PAY-001
"""
from datetime import UTC, datetime
from uuid import UUID

from app.adapters.entitlement_sandbox_adapter import EntitlementSandboxAdapter
from app.repositories.capability_status_repository import CapabilityStatusRepository
from app.repositories.payee_repository import PayeeRepository
from app.schemas.payees_schemas import CapabilityStatus, PayeeItem, PayeeListResponse


class PayeeService:
    """Service for payee business logic."""
    
    def __init__(
        self,
        payee_repo: PayeeRepository,
        capability_repo: CapabilityStatusRepository,
        entitlement_adapter: EntitlementSandboxAdapter
    ):
        self.payee_repo = payee_repo
        self.capability_repo = capability_repo
        self.entitlement_adapter = entitlement_adapter
    
    def get_saved_payees_for_customer(
        self,
        customer_profile_ref_id: UUID,
        page: int = 1,
        page_size: int = 20
    ) -> PayeeListResponse:
        """
        Get saved payees for a customer.
        
        Only payees with payee_status saved_active that entitlement allows are returned.
        When saved_payees capability is unavailable, response is 200 with empty page
        and capability message.
        
        Args:
            customer_profile_ref_id: Customer UUID
            page: Page number (1-based)
            page_size: Number of items per page
            
        Returns:
            PayeeListResponse with items, total, page, page_size, capability
        """
        # Check entitlement for payees (resource_type="payee", resource_reference="*")
        decision = self.entitlement_adapter.check_resource_access(
            customer_id=customer_profile_ref_id,
            resource_type="payee",
            resource_reference="*"
        )
        
        # Get capability status for saved_payees
        cap_record = self.capability_repo.get_current_status("saved_payees")
        
        # Build capability status
        capability = CapabilityStatus(
            capability_name="saved_payees",
            status_value=cap_record.status_value if cap_record else "unknown",
            customer_message_code=cap_record.customer_message_code if cap_record else None,
            customer_message=self._get_capability_message(cap_record),
            recovery_guidance=cap_record.recovery_guidance_code if cap_record else None,
            effective_from=cap_record.effective_from.isoformat() if cap_record and cap_record.effective_from else datetime.now(UTC).isoformat()
        )
        
        # If entitlement denied or capability unavailable, return empty page
        if decision != "allow" or (cap_record and cap_record.status_value == "unavailable"):
            return PayeeListResponse(
                items=[],
                total=0,
                page=page,
                page_size=page_size,
                capability=capability
            )
        
        # Get payees from repository
        payees, total = self.payee_repo.get_saved_active_payees_for_customer(
            customer_profile_ref_id=customer_profile_ref_id,
            page=page,
            page_size=page_size
        )
        
        # Map to response items
        items = [
            PayeeItem(
                payee_id=payee.id,
                payee_name=payee.payee_name,
                payee_sort_code=payee.payee_sort_code,
                masked_account_identifier=payee.masked_account_identifier
            )
            for payee in payees
        ]
        
        return PayeeListResponse(
            items=items,
            total=total,
            page=page,
            page_size=page_size,
            capability=capability
        )
    
    def _get_capability_message(self, cap_record) -> str:
        """Get capability message based on status."""
        if not cap_record:
            return "Saved payees status unknown"
        
        if cap_record.status_value == "healthy":
            return "Saved payees available"
        elif cap_record.status_value == "unavailable":
            return "Saved payees are currently unavailable. Please try again later."
        elif cap_record.status_value == "partial":
            return "Some saved payees may not be available"
        else:
            return f"Saved payees status: {cap_record.status_value}"

"""
Payees schemas for E-05 GET /api/v1/payees
Requirement: FR-PAY-001
"""
from uuid import UUID

from pydantic import BaseModel, ConfigDict


class PayeeItem(BaseModel):
    """
    One saved payee for selection.
    
    Fields:
    - payee_id: UUID of the payee
    - payee_name: Display name of payee
    - payee_sort_code: Sort code
    - masked_account_identifier: Masked account number (full number never shown)
    """
    payee_id: UUID
    payee_name: str
    payee_sort_code: str
    masked_account_identifier: str
    
    model_config = ConfigDict(from_attributes=True)


class CapabilityStatus(BaseModel):
    """
    Capability status for saved_payees capability.
    
    Fields:
    - capability_name: Name of the capability (saved_payees)
    - status_value: One of healthy, stale, partial, unavailable, restricted
    - customer_message_code: Optional message code
    - customer_message: Plain-language message
    - recovery_guidance: Optional recovery guidance
    - effective_from: When this status became effective
    """
    capability_name: str
    status_value: str
    customer_message_code: str | None = None
    customer_message: str
    recovery_guidance: str | None = None
    effective_from: str
    
    model_config = ConfigDict(from_attributes=True)


class PayeeListResponse(BaseModel):
    """
    Response for GET /api/v1/payees
    
    When saved_payees capability is unavailable, returns empty page with capability message.
    Only payees with payee_status saved_active that entitlement allows are returned.
    
    Fields:
    - items: List of PayeeItem (selectable payees)
    - total: Total number of selectable payees
    - page: Current page (1-based)
    - page_size: Page size used
    - capability: CapabilityStatus for saved_payees
    """
    items: list[PayeeItem]
    total: int
    page: int
    page_size: int
    capability: CapabilityStatus
    
    model_config = ConfigDict(from_attributes=True)

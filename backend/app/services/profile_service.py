"""
Profile management service for profile switching and business accounts.
Requirement: BR-ACCT-002, BR-ACCT-003, BR-ACCT-010, ADR-003
Release 2: One identity, many profiles
"""
import uuid

from fastapi import HTTPException, status
from sqlalchemy.orm import Session

from app.adapters.entitlement_sandbox_adapter import EntitlementSandboxAdapter
from app.models.business_profile_read_model import BusinessProfileReadModel
from app.models.customer_profile_ref import CustomerProfileRef
from app.schemas.profiles_schemas import (
    BusinessAccountItem,
    BusinessAccountsResponse,
    ProfilesResponse,
    ProfileSummary,
    SwitchProfileResponse,
)


class ProfileService:
    """Service for profile management and business accounts."""
    
    def __init__(
        self,
        db: Session,
        entitlement_adapter: EntitlementSandboxAdapter | None = None
    ):
        self.db = db
        self.entitlement_adapter = entitlement_adapter or EntitlementSandboxAdapter(db)
    
    def get_profiles(
        self,
        identity_reference: str,
        active_profile_id: uuid.UUID
    ) -> ProfilesResponse:
        """
        Get all profiles for an authenticated identity with at least one active entitlement.
        
        Per ADR-003: One identity, many profiles.
        Per BRL-ACCT-03: Show profile only if user has at least one active entitlement.
        
        Args:
            identity_reference: CIAM subject reference (identity across profiles)
            active_profile_id: Currently active profile ID
        
        Returns:
            ProfilesResponse with profiles having at least one active entitlement
        """
        # Get all profiles for this identity - CRITICAL: Filter by identity_reference (SEC-004)
        profiles_query = self.db.query(CustomerProfileRef).filter(
            CustomerProfileRef.ciam_subject_reference == identity_reference,
            CustomerProfileRef.is_active == True
        ).all()
        
        profile_summaries: list[ProfileSummary] = []
        
        for profile in profiles_query:
            # Check if user has any entitlement on this profile
            entitlements = self.entitlement_adapter.get_customer_entitlements(
                profile.id,
                resource_type=None
            )
            
            if not entitlements:
                # Per BRL-ACCT-03: Don't show profiles without active entitlements
                continue
            
            # Determine entitlement types
            has_view = any(e.decision == "allow" for e in entitlements)
            has_pay = any(
                e.decision == "allow" and 
                hasattr(e, 'entitlement_type') and 
                e.entitlement_type == "pay"
                for e in entitlements
            )
            
            profile_summaries.append(ProfileSummary(
                profile_id=str(profile.id),
                profile_type=profile.profile_type,
                display_name=profile.display_name,
                business_name=profile.business_name if profile.profile_type == "business" else None,
                is_active=profile.is_active,
                has_view_entitlement=has_view,
                has_pay_entitlement=has_pay
            ))
        
        return ProfilesResponse(
            profiles=profile_summaries,
            active_profile_id=str(active_profile_id)
        )
    
    def switch_profile(
        self,
        profile_id: str | uuid.UUID,
        identity_reference: str
    ) -> SwitchProfileResponse:
        """
        Switch active profile for authenticated user.
        
        Per ADR-003: Profile switch without re-authentication.
        Validates that profile belongs to identity and has active entitlements.
        
        Args:
            profile_id: Profile to switch to
            identity_reference: CIAM subject reference
        
        Returns:
            SwitchProfileResponse with new active profile details
        
        Raises:
            HTTPException: 403 if profile not accessible or no entitlements
            HTTPException: 404 if profile not found
        """
        # Convert profile_id to UUID if it's a string
        if isinstance(profile_id, str):
            try:
                profile_id = uuid.UUID(profile_id)
            except ValueError:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Invalid profile_id format"
                )
        
        # Get profile - CRITICAL: Verify profile belongs to identity (SEC-004 fix)
        profile = self.db.query(CustomerProfileRef).filter(
            CustomerProfileRef.id == profile_id,
            CustomerProfileRef.ciam_subject_reference == identity_reference,
            CustomerProfileRef.is_active == True
        ).first()
        
        if not profile:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Profile not found or not accessible"
            )
        
        # Verify user has entitlement on this profile (BRL-ACCT-03)
        entitlements = self.entitlement_adapter.get_customer_entitlements(
            profile_id,
            resource_type=None
        )
        
        if not entitlements or not any(e.decision == "allow" for e in entitlements):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Not entitled to access this profile"
            )
        
        return SwitchProfileResponse(
            active_profile_id=str(profile.id),
            profile_type=profile.profile_type,
            display_name=profile.display_name,
            business_name=profile.business_name if profile.profile_type == "business" else None
        )
    
    def get_business_accounts(
        self,
        customer_id: uuid.UUID
    ) -> BusinessAccountsResponse:
        """
        Get business accounts for active business profile.
        
        Per BR-ACCT-010: Business account shows business name, available balance,
        and pending outgoing payments.
        
        Args:
            customer_id: Business profile reference ID
        
        Returns:
            BusinessAccountsResponse with business accounts
        
        Raises:
            HTTPException: 404 if profile not found or not a business profile
        """
        # Get business profile
        profile = self.db.query(CustomerProfileRef).filter(
            CustomerProfileRef.id == customer_id,
            CustomerProfileRef.profile_type == "business",
            CustomerProfileRef.is_active == True
        ).first()
        
        if not profile:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Business profile not found"
            )
        
        # Get business account read models
        business_accounts = self.db.query(BusinessProfileReadModel).filter(
            BusinessProfileReadModel.customer_profile_ref_id == customer_id
        ).all()
        
        account_items: list[BusinessAccountItem] = []
        overall_state = "complete"
        
        for account in business_accounts:
            # Check if user has pay entitlement (BR-PAY-012)
            pay_decision = self.entitlement_adapter.check_resource_access(
                customer_id=customer_id,
                resource_type="account",
                resource_reference=str(account.id),
                entitlement_type="pay"
            )
            
            # Determine payment source eligibility based on pay entitlement
            has_pay_entitlement = (pay_decision == "allow")
            payment_source_eligible = (
                has_pay_entitlement and
                account.balance_availability_state == "current" and
                account.balance_amount_minor is not None
            )
            
            # Determine item state
            item_state = "available"
            if account.balance_availability_state in ("unavailable", "unknown"):
                item_state = "partial"
                overall_state = "partial"
            
            account_items.append(BusinessAccountItem(
                account_id=str(account.id),
                account_type=account.account_type,
                business_name=account.business_name,
                display_name=account.display_name,
                masked_account_identifier=account.masked_account_identifier,
                available_balance_minor=account.balance_amount_minor,
                currency=account.balance_currency,
                pending_outgoing_payments_count=account.pending_outgoing_payments_count,
                pending_outgoing_payments_amount_minor=account.pending_outgoing_payments_amount_minor,
                as_of_timestamp=account.as_of_timestamp,
                freshness_status=account.freshness_status,
                item_state=item_state,
                payment_source_eligible=payment_source_eligible
            ))
        
        return BusinessAccountsResponse(
            accounts=account_items,
            business_name=profile.business_name or profile.display_name,
            overview_state=overall_state
        )

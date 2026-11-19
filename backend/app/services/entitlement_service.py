"""Service for entitlement resolution."""
from sqlalchemy.orm import Session
from app.repositories.profile_repository import ProfileRepository
from app.adapters.entitlement_adapter import EntitlementAdapter


class EntitlementService:
    """Service for resolving profile entitlements."""

    def __init__(self, db: Session):
        self.db = db
        self.profile_repo = ProfileRepository(db)
        self.entitlement_adapter = EntitlementAdapter()

    def get_entitled_profiles(self, user_identity_id: int) -> list[dict]:
        """
        Get all profiles with their entitlements for a user.
        
        Returns list of dicts with profile info and entitlement flags.
        """
        profiles = self.profile_repo.get_profiles_by_user(user_identity_id)
        result = []
        
        for profile in profiles:
            # Get entitlements for this profile
            entitlements = self.profile_repo.get_entitlements_by_profile(profile.id)
            
            # Aggregate entitlements - any True means entitled
            can_view = any(e.can_view_accounts for e in entitlements)
            can_create = any(e.can_create_payee for e in entitlements)
            can_approve = any(e.can_approve_payment for e in entitlements)
            
            # Check external entitlement adapter (stub always returns True)
            external_check = self.entitlement_adapter.check_profile_entitlements(
                profile.id, user_identity_id
            )
            
            result.append({
                "profile_id": profile.id,
                "profile_type": profile.profile_type,
                "display_name": profile.display_name,
                "business_name": profile.business_name,
                "can_view_accounts": can_view and external_check["can_view_accounts"],
                "can_create_payee": can_create and external_check["can_create_payee"],
                "can_approve_payment": can_approve and external_check["can_approve_payment"]
            })
        
        return result

    def check_profile_access(self, profile_id: int, user_identity_id: int) -> bool:
        """Check if user has access to a profile."""
        profile = self.profile_repo.get_profile_by_id(profile_id)
        if not profile:
            return False
        return profile.user_identity_id == user_identity_id

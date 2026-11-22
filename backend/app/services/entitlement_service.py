"""Entitlement service with fail-safe enforcement"""
import uuid

from sqlalchemy.orm import Session

from app.core.errors import AuthorizationError
from app.repositories.entitlement_repository import EntitlementRepository


class EntitlementService:
    """Service for entitlement checks and enforcement"""

    def __init__(self):
        self.entitlement_repo = EntitlementRepository()

    def check_capability(
        self,
        db: Session,
        profile_id: uuid.UUID,
        capability: str,
        fail_safe: bool = True
    ) -> bool:
        """
        Check if profile has capability.

        Args:
            profile_id: Profile to check
            capability: One of 'view_accounts', 'manage_payees', 'initiate_payments'
            fail_safe: If True, deny on ambiguity or error; if False, raise exception

        Returns:
            True if profile has capability

        Raises:
            AuthorizationError: If fail_safe=False and check fails
        """
        try:
            has_capability = self.entitlement_repo.has_capability(db, profile_id, capability)
            if not has_capability and not fail_safe:
                raise AuthorizationError(f"Profile lacks {capability} capability")
            return has_capability
        except Exception:
            if fail_safe:
                # Fail safe: deny on error
                return False
            else:
                raise

    def require_capability(
        self,
        db: Session,
        profile_id: uuid.UUID,
        capability: str
    ) -> None:
        """
        Require profile to have capability (raises on failure).

        Raises:
            AuthorizationError: If profile lacks capability
        """
        if not self.check_capability(db, profile_id, capability, fail_safe=False):
            raise AuthorizationError(f"Profile lacks {capability} capability")

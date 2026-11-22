"""Entitlement repository"""
import uuid
from datetime import UTC, datetime

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.customer import Entitlement


class EntitlementRepository:
    """Repository for Entitlement operations"""

    def get_active_for_profile(self, db: Session, profile_id: uuid.UUID) -> list[Entitlement]:
        """Get active entitlements for a profile"""
        now = datetime.now(UTC)
        stmt = (
            select(Entitlement)
            .where(Entitlement.profile_id == profile_id)
            .where(
                (Entitlement.effective_from.is_(None)) | (Entitlement.effective_from <= now)
            )
            .where(
                (Entitlement.effective_to.is_(None)) | (Entitlement.effective_to > now)
            )
            .order_by(Entitlement.created_at)
        )
        result = db.execute(stmt)
        return list(result.scalars().all())

    def has_capability(
        self,
        db: Session,
        profile_id: uuid.UUID,
        capability: str
    ) -> bool:
        """
        Check if profile has specific capability.

        Args:
            capability: One of 'view_accounts', 'manage_payees', 'initiate_payments'
        """
        entitlements = self.get_active_for_profile(db, profile_id)

        if not entitlements:
            return False

        # Check any entitlement grants the capability
        for ent in entitlements:
            if capability == 'view_accounts' and ent.can_view_accounts:
                return True
            elif capability == 'manage_payees' and ent.can_manage_payees:
                return True
            elif capability == 'initiate_payments' and ent.can_initiate_payments:
                return True

        return False

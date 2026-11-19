"""Profile account visibility repository"""
import uuid
from typing import Optional

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.customer import ProfileAccountVisibility


class ProfileAccountVisibilityRepository:
    """Repository for ProfileAccountVisibility operations"""

    def get_by_profile_and_account(
        self,
        db: Session,
        profile_id: uuid.UUID,
        bank_account_id: uuid.UUID
    ) -> Optional[ProfileAccountVisibility]:
        """Get visibility mapping for profile and account"""
        stmt = select(ProfileAccountVisibility).where(
            ProfileAccountVisibility.profile_id == profile_id,
            ProfileAccountVisibility.bank_account_id == bank_account_id
        )
        result = db.execute(stmt)
        return result.scalar_one_or_none()

    def create_visibility(
        self,
        db: Session,
        visibility: ProfileAccountVisibility
    ) -> ProfileAccountVisibility:
        """Create visibility mapping"""
        db.add(visibility)
        return visibility

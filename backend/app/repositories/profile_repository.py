"""Profile repository"""
import uuid
from typing import Optional

from sqlalchemy import select
from sqlalchemy.orm import Session, joinedload

from app.models.customer import Profile


class ProfileRepository:
    """Repository for Profile operations"""

    def get_by_id(self, db: Session, profile_id: uuid.UUID) -> Optional[Profile]:
        """Get profile by ID with entitlements"""
        stmt = (
            select(Profile)
            .where(Profile.profile_id == profile_id)
            .options(joinedload(Profile.entitlements))
        )
        result = db.execute(stmt)
        return result.unique().scalar_one_or_none()

    def get_by_customer_id(self, db: Session, customer_id: uuid.UUID) -> list[Profile]:
        """Get all profiles for a customer"""
        stmt = (
            select(Profile)
            .where(Profile.customer_id == customer_id)
            .where(Profile.status == "active")
            .options(joinedload(Profile.entitlements))
            .order_by(Profile.created_at)
        )
        result = db.execute(stmt)
        return list(result.scalars().unique().all())

    def belongs_to_customer(self, db: Session, profile_id: uuid.UUID, customer_id: uuid.UUID) -> bool:
        """Check if profile belongs to customer"""
        stmt = select(Profile).where(
            Profile.profile_id == profile_id,
            Profile.customer_id == customer_id
        )
        result = db.execute(stmt)
        return result.scalar_one_or_none() is not None

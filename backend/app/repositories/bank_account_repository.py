"""Bank account repository"""
import uuid
from typing import Optional

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.customer import BankAccount, ProfileAccountVisibility


class BankAccountRepository:
    """Repository for BankAccount operations"""

    def get_by_id(self, db: Session, bank_account_id: uuid.UUID) -> Optional[BankAccount]:
        """Get bank account by ID"""
        return db.get(BankAccount, bank_account_id)

    def get_visible_for_profile(self, db: Session, profile_id: uuid.UUID) -> list[tuple[BankAccount, bool]]:
        """
        Get accounts visible to profile with payment permission flag.

        Returns:
            List of (BankAccount, payment_permission) tuples
        """
        stmt = (
            select(BankAccount, ProfileAccountVisibility.payment_permission)
            .join(
                ProfileAccountVisibility,
                ProfileAccountVisibility.bank_account_id == BankAccount.bank_account_id
            )
            .where(ProfileAccountVisibility.profile_id == profile_id)
            .where(
                (ProfileAccountVisibility.visible_from.is_(None))
                | (ProfileAccountVisibility.visible_from <= BankAccount.freshness_at)
            )
            .where(
                (ProfileAccountVisibility.visible_to.is_(None))
                | (ProfileAccountVisibility.visible_to > BankAccount.freshness_at)
            )
            .order_by(BankAccount.account_type, BankAccount.account_name)
        )
        result = db.execute(stmt)
        return list(result.all())

    def upsert_account(self, db: Session, account: BankAccount) -> BankAccount:
        """Insert or update bank account"""
        existing = db.get(BankAccount, account.bank_account_id)
        if existing:
            for key, value in account.__dict__.items():
                if not key.startswith('_'):
                    setattr(existing, key, value)
            return existing
        else:
            db.add(account)
            return account

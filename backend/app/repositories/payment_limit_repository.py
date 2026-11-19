"""PaymentLimit repository"""
import uuid
from datetime import datetime

from sqlalchemy import and_, select
from sqlalchemy.orm import Session

from ..models.payment import PaymentLimit


class PaymentLimitRepository:
    def __init__(self, db: Session):
        self.db = db

    def get_active_limits_for_profile(
        self,
        profile_id: uuid.UUID,
        now: datetime | None = None
    ) -> list[PaymentLimit]:
        if now is None:
            now = datetime.now(datetime.now().astimezone().tzinfo)

        result = self.db.execute(
            select(PaymentLimit)
            .where(
                and_(
                    PaymentLimit.profile_id == profile_id,
                    PaymentLimit.effective_from <= now,
                    (PaymentLimit.effective_to.is_(None) | (PaymentLimit.effective_to > now))
                )
            )
        )
        return list(result.scalars().all())

    def get_active_limits_for_account(
        self,
        bank_account_id: uuid.UUID,
        now: datetime | None = None
    ) -> list[PaymentLimit]:
        if now is None:
            now = datetime.now(datetime.now().astimezone().tzinfo)

        result = self.db.execute(
            select(PaymentLimit)
            .where(
                and_(
                    PaymentLimit.bank_account_id == bank_account_id,
                    PaymentLimit.effective_from <= now,
                    (PaymentLimit.effective_to.is_(None) | (PaymentLimit.effective_to > now))
                )
            )
        )
        return list(result.scalars().all())

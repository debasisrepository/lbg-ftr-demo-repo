"""RefCode repository"""
from sqlalchemy import and_, select
from sqlalchemy.orm import Session

from ..models.ref_code import RefCode


class RefCodeRepository:
    def __init__(self, db: Session):
        self.db = db

    def get_by_group_and_value(self, code_group: str, code_value: str) -> RefCode | None:
        result = self.db.execute(
            select(RefCode).where(
                and_(
                    RefCode.code_group == code_group,
                    RefCode.code_value == code_value,
                    RefCode.is_active.is_(True)
                )
            )
        )
        return result.scalar_one_or_none()

    def get_by_group(self, code_group: str) -> list[RefCode]:
        result = self.db.execute(
            select(RefCode)
            .where(
                and_(
                    RefCode.code_group == code_group,
                    RefCode.is_active == True
                )
            )
            .order_by(RefCode.sort_order)
        )
        return list(result.scalars().all())

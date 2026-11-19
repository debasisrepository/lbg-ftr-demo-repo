"""ScamClaim repository"""
from sqlalchemy import select
from sqlalchemy.orm import Session

from ..models.notification import ScamClaim


class ScamClaimRepository:
    def __init__(self, db: Session):
        self.db = db

    def create(self, claim: ScamClaim) -> ScamClaim:
        self.db.add(claim)
        self.db.flush()
        return claim

    def get_by_reference(self, claim_reference: str) -> ScamClaim | None:
        result = self.db.execute(
            select(ScamClaim).where(ScamClaim.claim_reference == claim_reference)
        )
        return result.scalar_one_or_none()

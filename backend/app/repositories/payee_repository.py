"""Repository for payee-related database operations."""
from datetime import datetime, timezone
from sqlalchemy.orm import Session
from app.models.payees import Payee, CoPResult


class PayeeRepository:
    """Repository for payee operations."""

    def __init__(self, db: Session):
        self.db = db

    def get_payees_by_profile(self, profile_id: int) -> list[Payee]:
        """Get all payees for a profile."""
        return self.db.query(Payee).filter(
            Payee.profile_id == profile_id
        ).all()

    def get_payee_by_id(self, payee_id: int) -> Payee | None:
        """Get payee by ID."""
        return self.db.query(Payee).filter(
            Payee.id == payee_id
        ).first()

    def create_payee(
        self,
        profile_id: int,
        display_name: str,
        nickname: str | None,
        sort_code: str,
        account_number_last4: str,
        account_number_hash: str,
        can_proceed: bool,
        created_in_journey: bool,
        payee_action_sca_verified_at: datetime | None
    ) -> Payee:
        """Create a new payee."""
        now = datetime.now(timezone.utc)
        payee = Payee(
            profile_id=profile_id,
            display_name=display_name,
            nickname=nickname,
            sort_code=sort_code,
            account_number_last4=account_number_last4,
            account_number_hash=account_number_hash,
            can_proceed=can_proceed,
            created_in_journey=created_in_journey,
            payee_action_sca_verified_at=payee_action_sca_verified_at,
            created_at=now,
            updated_at=now
        )
        self.db.add(payee)
        self.db.commit()
        self.db.refresh(payee)
        return payee

    def create_cop_result(
        self,
        payee_id: int,
        result_code: str,
        decision_state: str,
        provider_reference: str | None,
        returned_name: str | None,
        warning_message: str | None,
        checked_at: datetime
    ) -> CoPResult:
        """Create a CoP result record."""
        now = datetime.now(timezone.utc)
        cop = CoPResult(
            payee_id=payee_id,
            result_code=result_code,
            decision_state=decision_state,
            provider_reference=provider_reference,
            returned_name=returned_name,
            warning_message=warning_message,
            checked_at=checked_at,
            override_confirmed_at=None,
            created_at=now,
            updated_at=now
        )
        self.db.add(cop)
        self.db.commit()
        self.db.refresh(cop)
        return cop

    def get_latest_cop_result(self, payee_id: int) -> CoPResult | None:
        """Get latest CoP result for a payee."""
        return self.db.query(CoPResult).filter(
            CoPResult.payee_id == payee_id
        ).order_by(CoPResult.checked_at.desc()).first()

    def update_cop_override(self, cop_result_id: int) -> None:
        """Update CoP result with override confirmation."""
        cop = self.db.query(CoPResult).filter(
            CoPResult.id == cop_result_id
        ).first()
        if cop:
            now = datetime.now(timezone.utc)
            cop.decision_state = "confirmed"
            cop.override_confirmed_at = now
            cop.updated_at = now
            self.db.commit()

    def update_payee_can_proceed(self, payee_id: int, can_proceed: bool) -> None:
        """Update payee can_proceed flag."""
        payee = self.db.query(Payee).filter(
            Payee.id == payee_id
        ).first()
        if payee:
            payee.can_proceed = can_proceed
            payee.updated_at = datetime.now(timezone.utc)
            self.db.commit()

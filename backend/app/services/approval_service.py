"""Payment approval service"""
import uuid
from datetime import datetime, timedelta

from sqlalchemy.orm import Session

from ..models.payment import ScaApproval
from ..repositories.sca_approval_repository import ScaApprovalRepository
from ..repositories.step_up_repository import StepUpRepository
from ..services.dynamic_link_builder import DynamicLinkBuilder


class ApprovalService:
    """Handles SCA approval with dynamic linking"""

    def __init__(self, db: Session):
        self.db = db
        self.sca_approval_repo = ScaApprovalRepository(db)
        self.step_up_repo = StepUpRepository(db)

    def create_sca_approval(
        self,
        payment_order_id: uuid.UUID,
        device_id: uuid.UUID,
        source_account_id: uuid.UUID,
        payee_id: uuid.UUID,
        amount_minor: int,
        currency_code: str,
        payment_reference: str | None,
        correlation_id: str,
        step_up_challenge_ref: str | None = None
    ) -> ScaApproval:
        """Create SCA approval with dynamic linking"""

        # Build dynamic link digest
        dynamic_link_digest = DynamicLinkBuilder.build_digest(
            source_account_id,
            payee_id,
            amount_minor,
            currency_code,
            payment_reference
        )

        now = datetime.now(datetime.now().astimezone().tzinfo)
        expires_at = now + timedelta(minutes=5)  # 5-minute approval window

        # Determine approval method
        approval_method = "step_up_challenge" if step_up_challenge_ref else "passcode"

        sca_approval = ScaApproval(
            sca_approval_id=uuid.uuid4(),
            payment_order_id=payment_order_id,
            step_up_challenge_id=None,  # Link later if needed
            device_id=device_id,
            approval_method=approval_method,
            source_account_ref_snapshot=str(source_account_id),
            payee_ref_snapshot=str(payee_id),
            amount_minor_snapshot=amount_minor,
            currency_code_snapshot=currency_code,
            payment_reference_snapshot=payment_reference,
            dynamic_link_digest=dynamic_link_digest,
            approval_result="approved",
            approved_at=now,
            expires_at=expires_at,
            correlation_id=correlation_id,
            created_at=now
        )

        return self.sca_approval_repo.create(sca_approval)

    def verify_dynamic_link(
        self,
        sca_approval: ScaApproval,
        source_account_id: uuid.UUID,
        payee_id: uuid.UUID,
        amount_minor: int,
        currency_code: str,
        payment_reference: str | None
    ) -> bool:
        """Verify dynamic link digest matches payment parameters"""

        expected_digest = DynamicLinkBuilder.build_digest(
            source_account_id,
            payee_id,
            amount_minor,
            currency_code,
            payment_reference
        )

        return sca_approval.dynamic_link_digest == expected_digest

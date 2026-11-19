"""Scam claim service"""
import hashlib
import uuid
from datetime import datetime

from sqlalchemy.orm import Session

from ..adapters.fraud_case_adapter import get_fraud_case_adapter
from ..adapters.support_routing_adapter import get_support_routing_adapter
from ..core.errors import ValidationError
from ..models.notification import ScamClaim
from ..repositories.scam_claim_repository import ScamClaimRepository


class ScamClaimService:
    """Handles scam claim reporting"""

    def __init__(self, db: Session):
        self.db = db
        self.scam_claim_repo = ScamClaimRepository(db)
        self.fraud_case_adapter = get_fraud_case_adapter()
        self.support_routing_adapter = get_support_routing_adapter()

    def create_scam_claim(
        self,
        customer_id: uuid.UUID,
        payment_order_id: uuid.UUID | None,
        claim_reason_code: str,
        notes: str | None,
        correlation_id: str
    ) -> ScamClaim:
        """Create a new scam claim"""

        now = datetime.now(datetime.now().astimezone().tzinfo)

        # Generate claim reference
        claim_reference = f"SCM{uuid.uuid4().hex[:8].upper()}"

        # Create scam claim
        scam_claim = ScamClaim(
            scam_claim_id=uuid.uuid4(),
            customer_id=customer_id,
            payment_order_id=payment_order_id,
            claim_reference=claim_reference,
            claim_status="reported",
            claim_reason_code=claim_reason_code,
            reported_at=now,
            support_case_reference=None,
            fraud_case_reference=None,
            notes_digest=hashlib.sha256(notes.encode()).hexdigest() if notes else None,
            correlation_id=correlation_id,
            created_at=now,
            updated_at=now
        )

        scam_claim = self.scam_claim_repo.create(scam_claim)

        # Route to support
        support_response = self.support_routing_adapter.route_to_support({
            "claim_id": str(scam_claim.scam_claim_id),
            "customer_id": str(customer_id),
            "claim_reason_code": claim_reason_code
        })

        scam_claim.support_case_reference = support_response.support_case_reference

        # Create fraud case if payment involved
        if payment_order_id:
            fraud_response = self.fraud_case_adapter.create_case({
                "claim_id": str(scam_claim.scam_claim_id),
                "payment_order_id": str(payment_order_id),
                "claim_reason_code": claim_reason_code
            })
            scam_claim.fraud_case_reference = fraud_response.case_reference

        self.db.flush()

        return scam_claim

    def get_scam_claim(self, claim_reference: str) -> ScamClaim:
        """Get scam claim by reference"""
        scam_claim = self.scam_claim_repo.get_by_reference(claim_reference)
        if not scam_claim:
            raise ValidationError("Scam claim not found")
        return scam_claim

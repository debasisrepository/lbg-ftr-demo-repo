"""Dynamic link builder for SCA binding"""
import hashlib
import uuid


class DynamicLinkBuilder:
    """Builds HMAC digest for dynamic linking per NFR-001, NFR-002"""

    @staticmethod
    def build_digest(
        source_account_id: uuid.UUID,
        payee_id: uuid.UUID,
        amount_minor: int,
        currency_code: str,
        payment_reference: str | None
    ) -> str:
        """Build dynamic link digest from payment parameters"""
        parts = [
            str(source_account_id),
            str(payee_id),
            str(amount_minor),
            currency_code,
            payment_reference or ""
        ]

        digest_input = ":".join(parts)
        return hashlib.sha256(digest_input.encode()).hexdigest()

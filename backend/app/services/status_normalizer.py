"""Payment status normalization service"""


class StatusNormalizer:
    """Normalizes internal payment states to customer-facing status"""

    # Mapping of internal states to normalized status
    STATE_MAPPING = {
        "prepared": "pending",
        "awaiting_sca": "pending",
        "risk_held": "pending",
        "submitted": "sent",
        "duplicate_suspected": "pending",
        "notification_failed": "sent",
        "support_routed": "pending",
        "completed": "sent",
        "rejected": "failed",
    }

    @staticmethod
    def normalize(internal_state: str) -> str:
        """Normalize internal state to customer-facing status"""
        return StatusNormalizer.STATE_MAPPING.get(internal_state, "pending")

"""Protected actions models."""
import uuid
from datetime import datetime

from sqlalchemy import CheckConstraint, DateTime, String, Text, Uuid
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy.types import JSON

from app.database import Base


class ProtectedActionRequest(Base):
    """Protected action request."""

    __tablename__ = "protected_action_requests"

    id: Mapped[uuid.UUID] = mapped_column(Uuid, primary_key=True, default=uuid.uuid4)
    case_id: Mapped[uuid.UUID] = mapped_column(Uuid, nullable=False, index=True)
    customer_party_id: Mapped[str] = mapped_column(String(255), nullable=False, index=True)
    action_type: Mapped[str] = mapped_column(String(100), nullable=False)
    action_domain: Mapped[str] = mapped_column(String(50), nullable=False)
    action_payload_json: Mapped[dict] = mapped_column(JSON().with_variant(JSONB(), "postgresql"), nullable=False)
    request_status: Mapped[str] = mapped_column(String(50), nullable=False, default="pending_sca")
    requires_sca_flag: Mapped[bool] = mapped_column(default=True, nullable=False)
    sca_outcome: Mapped[str] = mapped_column(String(50), nullable=False, default="not_invoked")
    sca_invoked_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    sca_completed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    management_api_reference: Mapped[str | None] = mapped_column(String(255), nullable=True)
    fallback_guidance_text: Mapped[str | None] = mapped_column(Text, nullable=True)
    completed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    correlation_id: Mapped[str | None] = mapped_column(String(255), nullable=True, index=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)

    __table_args__ = (
        CheckConstraint(
            "action_domain IN ('card', 'money')",
            name="ck_action_domain",
        ),
        CheckConstraint(
            "request_status IN ('pending_sca', 'released', 'not_executed')",
            name="ck_request_status",
        ),
        CheckConstraint(
            "sca_outcome IN ('not_invoked', 'success', 'failed', 'abandoned')",
            name="ck_sca_outcome",
        ),
        CheckConstraint(
            "(request_status = 'pending_sca') OR (sca_outcome <> 'not_invoked')",
            name="ck_sca_outcome_when_not_pending",
        ),
    )

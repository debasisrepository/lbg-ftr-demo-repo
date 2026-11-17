"""Ownership and expected-by models."""
import uuid
from datetime import datetime

from sqlalchemy import Boolean, CheckConstraint, DateTime, Index, String, Text, Uuid
from sqlalchemy.orm import Mapped, mapped_column

from app.database import Base


class CaseOwnership(Base):
    """Time-bounded case ownership projection."""

    __tablename__ = "case_ownerships"

    id: Mapped[uuid.UUID] = mapped_column(Uuid, primary_key=True, default=uuid.uuid4)
    case_id: Mapped[uuid.UUID] = mapped_column(Uuid, nullable=False, index=True)
    owner_team_code: Mapped[str] = mapped_column(String(100), nullable=False)
    owner_semantic_label: Mapped[str] = mapped_column(String(100), nullable=False)
    owner_display_name: Mapped[str] = mapped_column(String(255), nullable=False)
    source_event_id: Mapped[uuid.UUID | None] = mapped_column(Uuid, nullable=True)
    effective_from: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    effective_to: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    is_current: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)

    __table_args__ = (
        Index(
            "ix_case_ownership_case_current",
            case_id,
            postgresql_where=(is_current == True),  # noqa: E712
            sqlite_where=(is_current == True),  # noqa: E712
            unique=True,
        ),
    )


class ExpectedByCommitment(Base):
    """Time-bounded expected-by commitment projection."""

    __tablename__ = "expected_by_commitments"

    id: Mapped[uuid.UUID] = mapped_column(Uuid, primary_key=True, default=uuid.uuid4)
    case_id: Mapped[uuid.UUID] = mapped_column(Uuid, nullable=False, index=True)
    commitment_state: Mapped[str] = mapped_column(String(50), nullable=False)
    expected_by_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    customer_explanatory_text: Mapped[str | None] = mapped_column(Text, nullable=True)
    confidence_basis: Mapped[str | None] = mapped_column(String(100), nullable=True)
    withdrawn_reason_code: Mapped[str | None] = mapped_column(String(100), nullable=True)
    source_event_id: Mapped[uuid.UUID | None] = mapped_column(Uuid, nullable=True)
    effective_from: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    effective_to: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    is_current: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)

    __table_args__ = (
        CheckConstraint(
            "commitment_state IN ('committed', 'revised', 'withdrawn', 'under_review')",
            name="ck_commitment_state",
        ),
        CheckConstraint(
            "(commitment_state IN ('committed', 'revised') AND expected_by_at IS NOT NULL) "
            "OR (commitment_state NOT IN ('committed', 'revised'))",
            name="ck_expected_by_date_required",
        ),
        Index(
            "ix_expected_by_case_current",
            case_id,
            postgresql_where=(is_current == True),  # noqa: E712
            sqlite_where=(is_current == True),  # noqa: E712
            unique=True,
        ),
    )

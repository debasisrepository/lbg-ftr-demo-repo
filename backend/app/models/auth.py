"""Authentication models."""
import uuid
from datetime import datetime

from sqlalchemy import CheckConstraint, DateTime, Index, Integer, String, Uuid
from sqlalchemy.orm import Mapped, mapped_column

from app.database import Base


class UserAccount(Base):
    """User account model."""

    __tablename__ = "user_accounts"

    id: Mapped[uuid.UUID] = mapped_column(Uuid, primary_key=True, default=uuid.uuid4)
    username: Mapped[str] = mapped_column(String(255), unique=True, nullable=False, index=True)
    hashed_password: Mapped[str] = mapped_column(String(255), nullable=False)
    email: Mapped[str | None] = mapped_column(String(255), nullable=True)
    display_name: Mapped[str | None] = mapped_column(String(255), nullable=True)
    scope: Mapped[str] = mapped_column(
        String(50), nullable=False, default="customer"
    )  # customer or colleague
    customer_party_id: Mapped[str | None] = mapped_column(String(255), nullable=True)
    colleague_reference: Mapped[str | None] = mapped_column(String(255), nullable=True)
    brand: Mapped[str | None] = mapped_column(String(50), nullable=True)  # lloyds or bank_of_scotland
    is_active: Mapped[bool] = mapped_column(default=True, nullable=False)
    failed_login_count: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    locked_until: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, default=lambda: datetime.now(datetime.now().tzinfo or None)
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        default=lambda: datetime.now(datetime.now().tzinfo or None),
        onupdate=lambda: datetime.now(datetime.now().tzinfo or None),
    )

    __table_args__ = (
        CheckConstraint("scope IN ('customer', 'colleague')", name="ck_user_scope"),
        CheckConstraint(
            "(scope = 'customer' AND customer_party_id IS NOT NULL) OR (scope = 'colleague' AND colleague_reference IS NOT NULL)",
            name="ck_user_scope_reference",
        ),
    )


class AuthSession(Base):
    """Authentication session model."""

    __tablename__ = "auth_sessions"

    id: Mapped[uuid.UUID] = mapped_column(Uuid, primary_key=True, default=uuid.uuid4)
    user_id: Mapped[uuid.UUID] = mapped_column(Uuid, nullable=False, index=True)
    token_hash: Mapped[str] = mapped_column(String(255), nullable=False, unique=True, index=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    expires_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    last_activity_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    revoked_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    revoke_reason: Mapped[str | None] = mapped_column(String(50), nullable=True)
    origin_channel: Mapped[str | None] = mapped_column(String(50), nullable=True)

    __table_args__ = (Index("ix_auth_sessions_user_active", user_id, revoked_at),)

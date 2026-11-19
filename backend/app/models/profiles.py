from datetime import datetime

from sqlalchemy import DateTime, ForeignKey, Index, Integer, String
from sqlalchemy.orm import Mapped, mapped_column

from app.common.enums import ProfileType
from app.database import Base


class UserProfile(Base):
    """User profile record (personal or business)."""
    __tablename__ = "user_profile"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    user_identity_id: Mapped[int] = mapped_column(Integer, ForeignKey("user_identity.id"), nullable=False)
    profile_type: Mapped[str] = mapped_column(String(20), nullable=False)
    display_name: Mapped[str] = mapped_column(String(255), nullable=False)
    business_name: Mapped[str | None] = mapped_column(String(255), nullable=True)
    external_profile_id: Mapped[str] = mapped_column(String(100), unique=True, nullable=False)
    is_default: Mapped[bool] = mapped_column(nullable=False, default=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)

    __table_args__ = (
        Index("ix_user_profile_user_identity_id", "user_identity_id"),
        Index("ix_user_profile_external_id", "external_profile_id"),
    )


class ProfileEntitlement(Base):
    """Profile entitlement record."""
    __tablename__ = "profile_entitlement"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    profile_id: Mapped[int] = mapped_column(Integer, ForeignKey("user_profile.id"), nullable=False)
    account_external_id: Mapped[str] = mapped_column(String(100), nullable=False)
    can_view_accounts: Mapped[bool] = mapped_column(nullable=False, default=True)
    can_create_payee: Mapped[bool] = mapped_column(nullable=False, default=False)
    can_approve_payment: Mapped[bool] = mapped_column(nullable=False, default=False)
    entitlement_source_version: Mapped[str | None] = mapped_column(String(50), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)

    __table_args__ = (
        Index("ix_profile_entitlement_profile_id", "profile_id"),
        Index("ix_profile_entitlement_account_external_id", "account_external_id"),
    )

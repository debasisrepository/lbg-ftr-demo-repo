from datetime import datetime

from sqlalchemy import DateTime, ForeignKey, Index, Integer, String
from sqlalchemy.orm import Mapped, mapped_column

from app.common.enums import SessionState, UserStatus
from app.database import Base


class UserIdentity(Base):
    """User identity record."""
    __tablename__ = "user_identity"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    external_identity_id: Mapped[str] = mapped_column(String(100), unique=True, nullable=False)
    username: Mapped[str] = mapped_column(String(255), unique=True, nullable=False)
    hashed_password: Mapped[str] = mapped_column(String(255), nullable=False)
    status: Mapped[str] = mapped_column(String(20), nullable=False, default=UserStatus.ACTIVE.value)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)

    __table_args__ = (
        Index("ix_user_identity_username", "username"),
        Index("ix_user_identity_external_id", "external_identity_id"),
    )


class AuthSession(Base):
    """Authentication session record."""
    __tablename__ = "auth_session"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    user_identity_id: Mapped[int] = mapped_column(Integer, ForeignKey("user_identity.id"), nullable=False)
    token_hash: Mapped[str] = mapped_column(String(64), unique=True, nullable=False)
    session_state: Mapped[str] = mapped_column(String(20), nullable=False, default=SessionState.ACTIVE.value)
    issued_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    expires_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    last_activity_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    active_profile_id: Mapped[int | None] = mapped_column(Integer, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)

    __table_args__ = (
        Index("ix_auth_session_user_identity_id", "user_identity_id"),
        Index("ix_auth_session_token_hash", "token_hash"),
        Index("ix_auth_session_state", "session_state"),
    )


class RegisteredDevice(Base):
    """Registered device record."""
    __tablename__ = "registered_device"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    user_identity_id: Mapped[int] = mapped_column(Integer, ForeignKey("user_identity.id"), nullable=False)
    device_id: Mapped[str] = mapped_column(String(100), unique=True, nullable=False)
    device_label: Mapped[str] = mapped_column(String(100), nullable=False)
    public_key_ref: Mapped[str | None] = mapped_column(String(255), nullable=True)
    biometric_enabled: Mapped[bool] = mapped_column(nullable=False, default=False)
    passcode_enabled: Mapped[bool] = mapped_column(nullable=False, default=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)

    __table_args__ = (
        Index("ix_registered_device_user_identity_id", "user_identity_id"),
        Index("ix_registered_device_device_id", "device_id"),
    )

from datetime import datetime, timezone
from sqlalchemy import String, Boolean, Integer, DateTime, CheckConstraint, Index, Text, Uuid
from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy.sql import func
import uuid
from app.database import Base
from app.core.clock import Clock


class AppUser(Base):
    __tablename__ = "app_user"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    email: Mapped[str] = mapped_column(String(255), nullable=False, unique=True)
    hashed_password: Mapped[str] = mapped_column(String(60), nullable=False)
    is_active: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
    is_colleague: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    customer_reference: Mapped[str | None] = mapped_column(String(64), nullable=True)
    brand: Mapped[str | None] = mapped_column(String(20), nullable=True)
    failed_login_count: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    account_locked_until: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    last_login_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, default=Clock.utc_now, server_default=func.current_timestamp())
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, default=Clock.utc_now, onupdate=Clock.utc_now, server_default=func.current_timestamp())

    __table_args__ = (
        CheckConstraint("is_colleague = FALSE OR customer_reference IS NULL", name="ck_app_user_colleague_no_customer"),
        CheckConstraint("brand IN ('lloyds', 'halifax', 'bos')", name="ck_app_user_brand"),
        Index("ix_app_user_email", "email"),
        Index("ix_app_user_customer_reference", "customer_reference"),
    )


class AuthSession(Base):
    __tablename__ = "auth_session"

    id: Mapped[uuid.UUID] = mapped_column(Uuid, primary_key=True)
    user_id: Mapped[int] = mapped_column(Integer, nullable=False)
    token_hash: Mapped[str] = mapped_column(String(64), nullable=False, unique=True)
    ip_address: Mapped[str | None] = mapped_column(String(45), nullable=True)
    user_agent: Mapped[str | None] = mapped_column(String(500), nullable=True)
    last_activity_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    expires_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    revoked: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, default=Clock.utc_now, server_default=func.current_timestamp())

    __table_args__ = (
        Index("ix_auth_session_user_id", "user_id"),
        Index("uq_auth_session_token_hash", "token_hash", unique=True),
    )


class LoginAttempt(Base):
    __tablename__ = "login_attempt"

    id: Mapped[uuid.UUID] = mapped_column(Uuid, primary_key=True)
    source_key: Mapped[str] = mapped_column(String(100), nullable=False)
    username_attempted: Mapped[str] = mapped_column(String(255), nullable=False)
    outcome: Mapped[str] = mapped_column(String(20), nullable=False)
    reason_code: Mapped[str | None] = mapped_column(String(40), nullable=True)
    ip_address: Mapped[str | None] = mapped_column(String(45), nullable=True)
    user_agent: Mapped[str | None] = mapped_column(String(500), nullable=True)
    occurred_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, default=Clock.utc_now, server_default=func.current_timestamp())

    __table_args__ = (
        CheckConstraint("outcome IN ('success', 'failed', 'locked', 'rate_limited')", name="ck_login_attempt_outcome"),
        Index("ix_login_attempt_source_key_occurred_at", "source_key", "occurred_at"),
    )

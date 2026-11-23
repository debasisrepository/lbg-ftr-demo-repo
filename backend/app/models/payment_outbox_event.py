"""PaymentOutboxEvent model - transactional outbox pattern for payment events."""
import uuid
from datetime import UTC, datetime

from sqlalchemy import (
    JSON,
    CheckConstraint,
    Column,
    ForeignKey,
    Index,
    Integer,
    String,
    UniqueConstraint,
)
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy.types import TypeDecorator

from app.database import Base


class JSONORJSONB(TypeDecorator[dict]):  # type: ignore[type-arg]
    """JSON type that uses JSONB for PostgreSQL and JSON for SQLite."""
    impl = JSON
    cache_ok = True
    
    def load_dialect_impl(self, dialect):  # type: ignore[no-untyped-def]
        if dialect.name == 'postgresql':
            return dialect.type_descriptor(JSONB())
        else:
            return dialect.type_descriptor(JSON())


class PaymentOutboxEvent(Base):
    """
    Payment outbox events - transactional outbox pattern.
    Written atomically with payment state transitions.
    """
    __tablename__ = "payment_outbox_events"
    
    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    payment_intent_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("payment_intents.id"), nullable=False)
    state_transition_id: Mapped[uuid.UUID | None] = mapped_column(nullable=True)  # FK not enforced due to stub
    event_sequence: Mapped[int] = mapped_column(Integer, CheckConstraint("event_sequence >= 1", name="ck_poe_sequence"), nullable=False)
    event_type: Mapped[str] = mapped_column(String(48), nullable=False)
    event_payload = Column(JSONORJSONB, nullable=False)
    publish_state: Mapped[str] = mapped_column(
        String(12),
        CheckConstraint("publish_state IN ('pending','published','failed','retrying')", name="ck_poe_publish_state"),
        default="pending",
        nullable=False
    )
    attempt_count: Mapped[int] = mapped_column(Integer, CheckConstraint("attempt_count >= 0", name="ck_poe_attempt_count"), default=0, nullable=False)
    next_attempt_at: Mapped[datetime | None] = mapped_column(nullable=True)
    last_error_code: Mapped[str | None] = mapped_column(String(48), nullable=True)
    published_at: Mapped[datetime | None] = mapped_column(nullable=True)
    event_stream_reference: Mapped[str | None] = mapped_column(String(128), nullable=True)
    correlation_id: Mapped[str | None] = mapped_column(String(64), nullable=True)
    created_at: Mapped[datetime] = mapped_column(default=lambda: datetime.now(UTC), nullable=False)
    updated_at: Mapped[datetime] = mapped_column(default=lambda: datetime.now(UTC), onupdate=lambda: datetime.now(UTC), nullable=False)
    
    __table_args__ = (
        UniqueConstraint('state_transition_id', name='uq_poe_state_transition'),
        Index('ix_poe_payment', 'payment_intent_id'),
        Index('ix_poe_publish_state', 'publish_state'),
        Index('ix_poe_next_attempt', 'next_attempt_at'),
        Index('ix_poe_correlation', 'correlation_id'),
    )

"""ConsumedEvent model - idempotent event consumption tracking."""
import uuid
from datetime import UTC, datetime

from sqlalchemy import CheckConstraint, Index, String
from sqlalchemy.orm import Mapped, mapped_column

from app.database import Base


class ConsumedEvent(Base):
    """
    Consumed events - tracks which events each consumer has processed.
    Prevents duplicate processing on replay.
    """
    __tablename__ = "consumed_events"
    
    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    consumer_name: Mapped[str] = mapped_column(
        String(32),
        CheckConstraint("consumer_name IN ('read_model_accounts','read_model_payments','status_and_flags','notifications')", name="ck_ce_consumer"),
        nullable=False
    )
    event_id: Mapped[str] = mapped_column(String(64), nullable=False)
    event_type: Mapped[str] = mapped_column(String(48), nullable=False)
    correlation_id: Mapped[str | None] = mapped_column(String(64), nullable=True)
    processed_at: Mapped[datetime] = mapped_column(default=lambda: datetime.now(UTC), nullable=False)
    
    __table_args__ = (
        Index('ix_ce_consumer_event', 'consumer_name', 'event_id', unique=True),
        Index('ix_ce_correlation', 'correlation_id'),
    )

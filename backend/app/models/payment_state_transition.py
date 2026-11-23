"""PaymentStateTransition stub"""
import uuid

from sqlalchemy import Column, Uuid

from app.database import Base


class PaymentStateTransition(Base):
    __tablename__ = "payment_state_transitions"
    id = Column(Uuid, primary_key=True, default=uuid.uuid4)

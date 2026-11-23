"""NotificationDeliveryAttempt stub"""
import uuid

from sqlalchemy import Column, Uuid

from app.database import Base


class NotificationDeliveryAttempt(Base):
    __tablename__ = "notification_delivery_attempts"
    id = Column(Uuid, primary_key=True, default=uuid.uuid4)

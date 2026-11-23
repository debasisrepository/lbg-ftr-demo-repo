"""NotificationTriggerRecord stub"""
import uuid

from sqlalchemy import Column, Uuid

from app.database import Base


class NotificationTriggerRecord(Base):
    __tablename__ = "notification_trigger_records"
    id = Column(Uuid, primary_key=True, default=uuid.uuid4)

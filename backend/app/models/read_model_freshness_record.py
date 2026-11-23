"""ReadModelFreshnessRecord stub"""
import uuid

from sqlalchemy import Column, Uuid

from app.database import Base


class ReadModelFreshnessRecord(Base):
    __tablename__ = "read_model_freshness_records"
    id = Column(Uuid, primary_key=True, default=uuid.uuid4)

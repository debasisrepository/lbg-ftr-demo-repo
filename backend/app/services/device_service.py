"""Device management service"""
import uuid

from sqlalchemy.orm import Session

from ..repositories.device_repository import DeviceRepository


class DeviceService:
    """Device trust and passcode management"""

    def __init__(self, db: Session):
        self.db = db
        self.device_repo = DeviceRepository(db)

    def get_device(self, device_id: uuid.UUID) -> object | None:
        """Get device by ID"""
        return self.device_repo.get_by_id(device_id)

    def get_customer_device(self, customer_id: uuid.UUID, device_id: uuid.UUID) -> object | None:
        """Get device belonging to customer"""
        return self.device_repo.get_customer_device(customer_id, device_id)

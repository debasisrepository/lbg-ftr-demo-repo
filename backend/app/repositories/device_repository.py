"""Device repository for device trust and passcode management"""
import uuid
from datetime import UTC, datetime

from sqlalchemy import select
from sqlalchemy.orm import Session

from ..models.customer import Device


class DeviceRepository:
    """Device data access"""

    def __init__(self, db: Session):
        self.db = db

    def get_by_id(self, device_id: uuid.UUID) -> Device | None:
        """Get device by ID"""
        return self.db.get(Device, device_id)

    def get_customer_device(self, customer_id: uuid.UUID, device_id: uuid.UUID) -> Device | None:
        """Get device belonging to customer"""
        stmt = select(Device).where(
            Device.device_id == device_id,
            Device.customer_id == customer_id
        )
        result = self.db.execute(stmt)
        return result.scalar_one_or_none()

    def get_trusted_device(self, customer_id: uuid.UUID, device_id: uuid.UUID) -> Device | None:
        """Get trusted device belonging to customer"""
        stmt = select(Device).where(
            Device.device_id == device_id,
            Device.customer_id == customer_id,
            Device.trust_state == 'trusted',
            Device.revoked_at.is_(None)
        )
        result = self.db.execute(stmt)
        return result.scalar_one_or_none()

    def increment_passcode_failed_count(self, device: Device) -> None:
        """Increment passcode failed count"""
        device.passcode_failed_count += 1
        device.updated_at = datetime.now(UTC)
        self.db.flush()

    def reset_passcode_failed_count(self, device: Device) -> None:
        """Reset passcode failed count on successful auth"""
        device.passcode_failed_count = 0
        device.passcode_paused_until = None
        device.updated_at = datetime.now(UTC)
        self.db.flush()

    def pause_passcode(self, device: Device, pause_until: datetime) -> None:
        """Pause passcode entry after too many failures"""
        device.passcode_paused_until = pause_until
        device.updated_at = datetime.now(UTC)
        self.db.flush()

    def update_last_seen(self, device: Device) -> None:
        """Update device last seen timestamp"""
        device.last_seen_at = datetime.now(UTC)
        device.updated_at = datetime.now(UTC)
        self.db.flush()

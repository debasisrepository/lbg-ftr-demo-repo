"""Service status service"""
from sqlalchemy.orm import Session

from ..models.notification import ServiceStatusNotice
from ..repositories.service_status_notice_repository import ServiceStatusNoticeRepository


class ServiceStatusService:
    """Handles service status notices"""

    def __init__(self, db: Session):
        self.db = db
        self.service_status_repo = ServiceStatusNoticeRepository(db)

    def get_active_notices(self) -> list[ServiceStatusNotice]:
        """Get currently active service status notices"""
        return self.service_status_repo.get_active_notices()

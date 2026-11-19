"""ServiceStatusNotice repository"""
from datetime import datetime

from sqlalchemy import and_, select
from sqlalchemy.orm import Session

from ..models.notification import ServiceStatusNotice


class ServiceStatusNoticeRepository:
    def __init__(self, db: Session):
        self.db = db

    def get_active_notices(self, now: datetime | None = None) -> list[ServiceStatusNotice]:
        if now is None:
            now = datetime.now(datetime.now().astimezone().tzinfo)

        result = self.db.execute(
            select(ServiceStatusNotice)
            .where(
                and_(
                    ServiceStatusNotice.starts_at <= now,
                    (ServiceStatusNotice.ends_at.is_(None) | (ServiceStatusNotice.ends_at > now))
                )
            )
            .order_by(ServiceStatusNotice.starts_at.desc())
        )
        return list(result.scalars().all())

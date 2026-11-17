from datetime import datetime
from pydantic import BaseModel, ConfigDict
import uuid


class NotificationRecordCreate(BaseModel):
    case_id: uuid.UUID
    event_id: uuid.UUID
    template_ref: str
    reentry_route: str
    privacy_classification: str = "generic"


class NotificationRecordView(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    case_id: uuid.UUID
    event_id: uuid.UUID
    template_ref: str
    reentry_route: str
    privacy_classification: str
    status: str
    requested_at: datetime
    dispatched_at: datetime | None

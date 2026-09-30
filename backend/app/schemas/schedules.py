import uuid
from datetime import datetime

from pydantic import BaseModel


class ScheduleCreate(BaseModel):
    action: str
    cadence: str
    module_id: uuid.UUID | None = None
    target_roles: list[str] = []


class ScheduleResponse(BaseModel):
    id: uuid.UUID
    action: str
    cadence: str
    module_id: uuid.UUID | None
    target_roles: list[str]
    is_active: bool
    last_triggered_at: datetime | None
    created_at: datetime

    model_config = {"from_attributes": True}

import uuid
from datetime import datetime

from pydantic import BaseModel

from app.schemas.common import ProgressStatus


class AssignRequest(BaseModel):
    user_id: uuid.UUID
    module_id: uuid.UUID


class ProgressUpdate(BaseModel):
    status: ProgressStatus
    score: int | None = None


class ProgressResponse(BaseModel):
    id: uuid.UUID
    user_id: uuid.UUID
    module_id: uuid.UUID
    status: ProgressStatus
    score: int | None = None
    completed_at: datetime | None = None

    model_config = {"from_attributes": True}

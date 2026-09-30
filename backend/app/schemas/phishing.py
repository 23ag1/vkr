import uuid
from datetime import datetime

from pydantic import BaseModel

from app.schemas.common import CampaignStatus, Difficulty


class TemplateCreate(BaseModel):
    name: str
    subject: str
    body_html: str
    difficulty: Difficulty = Difficulty.MEDIUM


class TemplateUpdate(BaseModel):
    name: str | None = None
    subject: str | None = None
    body_html: str | None = None
    difficulty: Difficulty | None = None


class TemplateResponse(BaseModel):
    id: uuid.UUID
    name: str
    subject: str
    body_html: str
    difficulty: Difficulty

    model_config = {"from_attributes": True}


class CampaignCreate(BaseModel):
    name: str
    template_id: uuid.UUID
    user_ids: list[uuid.UUID] = []


class CampaignResponse(BaseModel):
    id: uuid.UUID
    name: str
    template_id: uuid.UUID
    status: CampaignStatus
    created_by: uuid.UUID | None = None

    model_config = {"from_attributes": True}


class RecipientResult(BaseModel):
    id: uuid.UUID
    user_id: uuid.UUID
    tracking_token: str
    clicked_at: datetime | None = None
    reported_at: datetime | None = None

    model_config = {"from_attributes": True}


class InboxItem(BaseModel):
    id: uuid.UUID
    tracking_token: str
    clicked_at: datetime | None = None
    reported_at: datetime | None = None
    created_at: datetime
    campaign_name: str
    campaign_status: str
    subject: str
    body_html: str
    difficulty: str

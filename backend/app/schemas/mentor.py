import uuid
from typing import Any

from pydantic import BaseModel


class SessionCreate(BaseModel):
    title: str = "New Chat"
    module_id: uuid.UUID | None = None


class SessionResponse(BaseModel):
    id: uuid.UUID
    user_id: uuid.UUID
    module_id: uuid.UUID | None = None
    title: str

    model_config = {"from_attributes": True}


class MessageCreate(BaseModel):
    content: str


class MessageResponse(BaseModel):
    id: uuid.UUID
    session_id: uuid.UUID
    role: str
    content: str
    sources: Any | None = None

    model_config = {"from_attributes": True}

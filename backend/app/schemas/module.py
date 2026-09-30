import uuid

from pydantic import BaseModel


BRIEFING_TYPES = {"none", "introductory", "primary", "repeated", "extraordinary"}


class ModuleCreate(BaseModel):
    title: str
    description: str = ""
    content_md: str = ""
    target_roles: list[str] = []
    order_index: int = 0
    briefing_type: str = "none"


class ModuleUpdate(BaseModel):
    title: str | None = None
    description: str | None = None
    content_md: str | None = None
    target_roles: list[str] | None = None
    order_index: int | None = None
    briefing_type: str | None = None


class ModuleResponse(BaseModel):
    id: uuid.UUID
    title: str
    description: str
    content_md: str
    target_roles: list[str]
    order_index: int
    is_published: bool
    briefing_type: str = "none"

    model_config = {"from_attributes": True}

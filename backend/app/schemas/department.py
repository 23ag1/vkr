import uuid

from pydantic import BaseModel


class DepartmentCreate(BaseModel):
    name: str
    parent_id: uuid.UUID | None = None


class DepartmentUpdate(BaseModel):
    name: str | None = None
    parent_id: uuid.UUID | None = None


class DepartmentResponse(BaseModel):
    id: uuid.UUID
    name: str
    parent_id: uuid.UUID | None = None

    model_config = {"from_attributes": True}

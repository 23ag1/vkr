import uuid
from datetime import datetime

from pydantic import BaseModel, EmailStr, field_validator

from app.schemas.common import Role


class UserCreate(BaseModel):
    email: EmailStr
    password: str
    full_name: str
    role: Role = Role.EMPLOYEE
    department_id: uuid.UUID | None = None

    @field_validator("password")
    @classmethod
    def password_min_length(cls, v: str) -> str:
        if len(v) < 8:
            raise ValueError("password must be at least 8 characters")
        return v


class UserUpdate(BaseModel):
    email: EmailStr | None = None
    full_name: str | None = None
    role: Role | None = None
    department_id: uuid.UUID | None = None
    is_active: bool | None = None


class UserResponse(BaseModel):
    id: uuid.UUID
    email: str
    full_name: str
    role: str
    is_active: bool
    department_id: uuid.UUID | None = None
    diagnostic_completed_at: datetime | None = None

    model_config = {"from_attributes": True}

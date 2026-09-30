from enum import StrEnum
from typing import Generic, TypeVar

from pydantic import BaseModel

T = TypeVar("T")


class Role(StrEnum):
    EMPLOYEE = "employee"
    ADMIN = "admin"
    SECURITY_SPECIALIST = "security_specialist"
    MANAGER = "manager"


class ProgressStatus(StrEnum):
    NOT_STARTED = "not_started"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"


class Difficulty(StrEnum):
    EASY = "easy"
    MEDIUM = "medium"
    HARD = "hard"


class CampaignStatus(StrEnum):
    DRAFT = "draft"
    ACTIVE = "active"
    COMPLETED = "completed"


class ApiResponse(BaseModel, Generic[T]):
    data: T | None = None
    error: str | None = None


class PaginatedMeta(BaseModel):
    total: int
    page: int = 1
    limit: int = 20


class PaginatedResponse(BaseModel, Generic[T]):
    data: list[T]
    error: str | None = None
    meta: PaginatedMeta


def ok(payload: T) -> ApiResponse[T]:
    return ApiResponse(data=payload, error=None)


def err(message: str) -> ApiResponse[None]:
    return ApiResponse(data=None, error=message)


def paginated(items: list[T], total: int, page: int = 1, limit: int = 20) -> PaginatedResponse[T]:
    return PaginatedResponse(data=items, error=None, meta=PaginatedMeta(total=total, page=page, limit=limit))

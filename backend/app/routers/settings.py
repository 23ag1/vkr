from fastapi import APIRouter, Depends
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession

import app.services.audit as audit_service
import app.services.config_store as config_store
from app.deps import get_db, require_role
from app.models.user import User
from app.schemas.common import ApiResponse, ok

router = APIRouter()
_admin = Depends(require_role("admin"))


class SettingsBody(BaseModel):
    question_prompt: str | None = None
    explanation_prompt: str | None = None
    model: str | None = None


@router.get("/", response_model=ApiResponse[dict], dependencies=[_admin])
async def get_settings():
    return ok(config_store.get_all())


@router.patch("/", response_model=ApiResponse[dict])
async def update_settings(
    body: SettingsBody,
    current_user: User = Depends(require_role("admin")),
    db: AsyncSession = Depends(get_db),
):
    changes = body.model_dump(exclude_none=True)
    updated = config_store.update(changes)
    await audit_service.write(db, user_id=current_user.id, action="settings_changed", details={"keys": list(changes.keys())})
    return ok(updated)
